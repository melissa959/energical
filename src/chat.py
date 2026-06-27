import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from sentence_transformers import SentenceTransformer
from src.chat_history import ChatHistory
from src.conversation_memory import ConversationMemory
from src.memory_extractor import MemoryExtractor
from src.turn_manager import TurnManager
from src.dialogue_loader import DialogueLoader
from src.dialogue_retriever import DialogueRetriever
from src.query_builder import QueryBuilder

from business.process_business_rules import BusinessRecommendationEngine
from llm.groq_client import (
    is_discovery_intent,
    is_vague_message,
    _session as groq_session,
    reset_session as groq_reset_session,
)
from rag.retrieval import retrieve

CHROMA_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "chroma_db")
)
COLLECTION_NAME = "energical_catalog"

# ------------------------------------------------------------------
# Keyword -> normalized category
# ------------------------------------------------------------------
KEYWORD_TO_CATEGORY = {
    # Chaudiere / chauffage
    "chaudiere":     "chaudiere",
    "chaudière":     "chaudiere",
    "chauffage":     "chaudiere",
    "chaufage":      "chaudiere",
    "chauffe eau":   "chaudiere",
    "chauffe-eau":   "chaudiere",
    "skhana":        "chaudiere",
    "sekhan":        "chaudiere",
    "choufage":      "chaudiere",
    # Climatisation
    "clim":          "climatisation",
    "climatiseur":   "climatisation",
    "climatisation": "climatisation",
    "clima":         "climatisation",
    "baroud":        "climatisation",
    # Robinetterie
    "robinet":       "robinetterie",
    "mitigeur":      "robinetterie",
    "robinetterie":  "robinetterie",
    # Visiophone
    "visiophone":    "visiophone",
    "interphone":    "visiophone",
    "sonnette":      "visiophone",
    "badge":         "visiophone",
    "rfid":          "visiophone",
}

# Produits hors-sujet a exclure selon categorie
IRRELEVANT_BY_CATEGORY = {
    "chaudiere": ["friteuse", "four", "aspirateur", "cafetiere", "congelateur",
                  "refrigerateur", "micro-onde", "electromenager"],
    "climatisation": ["friteuse", "four", "aspirateur", "chaudiere", "robinet",
                      "mitigeur", "visiophone"],
    "robinetterie": ["friteuse", "four", "climatiseur", "chaudiere", "visiophone"],
    "visiophone": ["friteuse", "four", "climatiseur", "chaudiere", "robinet"],
}


def detect_category_from_text(text: str) -> str:
    text_lower = text.lower()
    for keyword in sorted(KEYWORD_TO_CATEGORY.keys(), key=len, reverse=True):
        if keyword in text_lower:
            return KEYWORD_TO_CATEGORY[keyword]
    return ""


def filter_products_by_category(products: list, category: str) -> list:
    """Enleve les produits hors-sujet pour la categorie donnee."""
    if not category or not products:
        return products

    noise_words = IRRELEVANT_BY_CATEGORY.get(category, [])
    if not noise_words:
        return products

    filtered = []
    for p in products:
        nom  = p.get("metadata", {}).get("nom", "").lower()
        desc = p.get("document_text", "").lower()
        full = nom + " " + desc
        if not any(noise in full for noise in noise_words):
            filtered.append(p)

    # Si le filtre vide tout (cas rare), retourner l'original
    return filtered if filtered else products


class ChatManager:

    def __init__(self):
        self.history  = ChatHistory()
        self.memory   = ConversationMemory()
        self.turns    = TurnManager()

        dialogues_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "docs", "dialogues_propres.json"
        ))
        loader = DialogueLoader(dialogues_path)
        self.dialogue_retriever = DialogueRetriever(loader.get_dialogues())
        self.query_builder      = QueryBuilder()

        chroma_client   = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        self.collection = chroma_client.get_collection(name=COLLECTION_NAME)
        self.model      = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        self.engine = BusinessRecommendationEngine()

        # Categorie stable persistee dans l'instance (pas de variable globale)
        self.stable_category = ""
        self.asked_fields    = set()

    def _resolve_category(
        self,
        user_message: str,
        dialogue_result: dict,
        retrieved_products: list
    ) -> str:
        """
        Priorite :
        1. Mot-cle dans le message actuel
        2. Categorie stable de la conversation
        3. Dialogue retriever
        4. Metadata RAG
        """
        # 1. Message actuel
        from_text = detect_category_from_text(user_message)
        if from_text:
            self.stable_category = from_text
            groq_session["current_category"] = from_text
            return from_text

        # 2. Memoire conversation
        if self.stable_category:
            return self.stable_category

        # 3. Dialogue retriever
        family = dialogue_result.get("family", "")
        if family:
            self.stable_category = family
            groq_session["current_category"] = family
            return family

        # 4. RAG metadata
        if retrieved_products:
            cat = retrieved_products[0]["metadata"].get("categorie", "")
            nom = retrieved_products[0]["metadata"].get("nom", "")
            from_rag = detect_category_from_text(cat + " " + nom)
            if from_rag:
                self.stable_category = from_rag
                groq_session["current_category"] = from_rag
                return from_rag

        return ""

    def _filter_already_asked(self, missing_fields: list) -> list:
        return [f for f in missing_fields if f not in self.asked_fields]

    def send_message(self, user_message: str) -> dict:

        # 1. Historique et memoire
        self.history.add_user(user_message)
        extracted = MemoryExtractor.extract(user_message)
        if isinstance(extracted, dict):
            self.memory.update(**extracted)

        self.turns.increment()
        turn_count = self.turns.get_turn_count()

        # 2. RAG query
        dialogue_result = self.dialogue_retriever.retrieve(user_message)

        if turn_count == 1 or len(user_message.split()) <= 3:
            query = user_message
        else:
            query = self.query_builder.build_query(
                user_message=user_message,
                memory=self.memory,
                dialogue_result=dialogue_result,
            )

        # 3. Retrieval
        retrieved_products = retrieve(
            query=query,
            chat_history=self.history.get_history(),
            model=self.model,
            collection=self.collection,
            k=5
        )

        # 4. Categorie
        mem = self.memory.to_dict()

        # Message vague au premier tour : pas de categorie, pas de produits
        if is_vague_message(user_message) and turn_count == 1:
            category           = ""
            retrieved_products = []
        else:
            category = self._resolve_category(user_message, dialogue_result, retrieved_products)

        # 5. Filtrer les produits hors-sujet AVANT de passer au moteur
        if category:
            retrieved_products = filter_products_by_category(retrieved_products, category)

        # 6. Discovery intent
        discovery = is_discovery_intent(user_message)

        # 7. Moteur business
        business_result = self.engine.process_business_rules(
            category=category,
            collected_information=mem,
            turn_count=turn_count,
            retrieved_products=retrieved_products,
            user_question=user_message,
        )

        # 8. Filtrer champs deja poses
        remaining_missing = self._filter_already_asked(
            business_result.get("missing_information", [])
        )
        business_result["missing_information"] = remaining_missing

        if remaining_missing:
            self.asked_fields.add(remaining_missing[0])

        # 9. Reponse LLM
        llm_final_reply = business_result["llm_answer"]
        self.history.add_assistant(llm_final_reply)

        return {
            "user_message":         user_message,
            "memory":               mem,
            "turn_count":           turn_count,
            "dialogue":             dialogue_result,
            "retrieval_query":      query,
            "chat_history":         self.history.get_history(),
            "retrieved_products":   retrieved_products,
            "business_status":      business_result["status"],
            "allow_recommendation": business_result["allow_recommendation"],
            "llm_answer":           llm_final_reply,
            "missing_information":  remaining_missing,
            "discovery_intent":     discovery,
        }