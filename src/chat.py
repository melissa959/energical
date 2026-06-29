

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from sentence_transformers import SentenceTransformer

from src.chat_history        import ChatHistory
from src.conversation_memory import ConversationMemory
from src.memory_extractor    import MemoryExtractor
from src.turn_manager        import TurnManager
from src.dialogue_loader     import DialogueLoader
from src.dialogue_retriever  import DialogueRetriever

from business.process_business_rules import BusinessRecommendationEngine
from llm.groq_client import (
    generate_answer,
    detect_category,
    is_vague_message,
    is_discovery_intent,
    _session as groq_session,
    reset_session as groq_reset,
)
from rag.retrieval import retrieve

CHROMA_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "chroma_db")
)
COLLECTION_NAME = "energical_catalog"


_NORMALIZATIONS = [
    (r'\butane\b|\bboutane\b|\bbutanee?\b|\buutane\b|\butanne\b', 'butane'),
    (r'\bgaz\s*nat\w*\b|\bgaz\s+naturel\b|\bnatural\s*gas\b',    'gaz naturel'),
    (r'\belectricit[eé]\b|\belectrique\b|\belec\b|\belect\b',    'electricite'),
    (r'\b(\d+)\s*(m2|m²|metre[s]?\s*carr[eé][s]?|metros?)\b',   lambda m: m.group(1) + ' m2'),
    (r'\b(oui|yep|iyeh|yes|aya)\b',                              'oui'),
    (r'\b(non|no|la|nein|walou)\b',                              'non'),
    (r'\bcondensation\b|\bcondensant\b|\bcondens\b',             'condensation'),
    (r'\bappart(ement)?\b|\baptos?\b',                           'appartement'),
    (r'\bmaison\b|\bvilla\b|\bdar\b',                            'maison'),
]

def _normalize_input(text: str) -> str:
    t = text.lower().strip()
    for pattern, replacement in _NORMALIZATIONS:
        if callable(replacement):
            t = re.sub(pattern, replacement, t)
        else:
            t = re.sub(pattern, replacement, t)
    return t




_COURTESY_PATTERNS = [
    r'^(merci|mercii+|thx|thank(s| you)|shukran|choukran|barak\s*allah|wach\s*rak)[\s!.]*$',
    r'^(ok|okay|d\'accord|dac|oki|okk|ça\s*marche|ca\s*marche|parfait|super|genial|nickel)[\s!.]*$',
    r'^(bien|tres\s+bien|bonne\s+continuation|au\s+revoir|bye|salam|bonne\s+journee)[\s!.]*$',
    r'^(c\'?est\s+(bon|clair|ok|tout|suffisant)|j\'ai\s+compris|compris|je\s+vois)[\s!.]*$',
]

def _is_courtesy(text: str) -> bool:
    t = text.lower().strip()
    for p in _COURTESY_PATTERNS:
        if re.match(p, t):
            return True
    return False



_QUERY_NOISE = [
    "svp", "stp", "please", "merci", "ok", "oui", "non",
    "je veux", "je cherche", "bghit", "nheb", "donne moi",
    "pouvez vous", "pourriez vous", "aidez moi", "aide moi",
]



_MEMORY_ANSWER_PATTERNS = [
    r'^\d+\s*(m2|metres?(\s*carr[eé]s?)?|m²)?$',
    r'^(gaz(\s+naturel)?|butane|electricite|electrique)$',
    r'^(oui|non|yes|no|iyeh|la)$',
    r'^(appartement|maison|villa|local|bureau|commerce)$',
    r'^(nord|sud|est|ouest|alger|oran|constantine|annaba|setif|blida|tlemcen)$',
    r'^(instantane|accumulation|reservoir)$',
    r'^\d+\s*(kw|kilowatt)$',
    r'^(collectif|individuel)$',
    r'^condensation$',
]

def _is_memory_answer(text: str) -> bool:
    t = _normalize_input(text)
    if len(t.split()) <= 3 and not detect_category(t):
        for pattern in _MEMORY_ANSWER_PATTERNS:
            if re.match(pattern, t):
                return True
        if len(t.split()) <= 2:
            return True
    return False




_FOLLOWUP_PATTERNS = [
    r"quel(le)?\s+(est|sont)\s+(le|la|les)?\s*(meilleur|mieux|plus)",
    r"lequel", r"laquelle",
    r"compare", r"diff[eé]rence",
    r"plus\s+de\s+d[eé]tails?", r"d[eé]tails?\s+sur",
    r"parle\s+moi\s+du?e?",
    r"c'est\s+quoi\s+exactement",
    r"expliqu",
    r"tu\s+me\s+conseilles?",
    r"je\s+prends?\s+lequel",
    r"entre\s+(les|ces|les\s+deux|les\s+trois)",
    r"tu\s+m('|e)\s*a\s+propos[eé]",
    r"les\s+\d+\s+que\s+tu",
    r"ces\s+produits?",
    r"celui[- ]ci|celui[- ]l[aà]",
    r"celle[- ]ci|celle[- ]l[aà]",
    r"ce\s+produit", r"ce\s+mod[eè]le",
    r"c'est\s+le\s+numero", r"numero\s+\d",
    r"le\s+premier|le\s+deuxi[eè]me|le\s+troisi[eè]me",
    r"la\s+premi[eè]re|la\s+deuxi[eè]me|la\s+troisi[eè]me",
    r"comment\s+je\s+choisis", r"comment\s+choisir",
    r"c'est\s+quoi\s+la\s+diff",
    r"je\s+prends\s+quoi",
    r"vous\s+me\s+conseillez\s+quoi",
    r"de\s+quoi\s+tu\s+me\s+conseille",
    r"je\s+peux\s+avoir\s+plus\s+de\s+d[eé]tails?",
    r"plus\s+d'infos?",
    r"(c'est\s+quoi|quel(\s+est)?|combien)\s+(le|la|son|leur)?\s*prix",
    r"combien\s+(ca|ça|il|elle)\s+(co[uû]te?|vaut|fait)",
    r"le\s+prix\s+de\s+celle", r"le\s+prix\s+de\s+celui",
    r"donne\s+moi\s+le\s+prix",
    r"c'est\s+combien", r"il\s+co[uû]te\s+combien",
    r"le\s+tarif",
   
    r"^(donne[- ]moi\s+)?(plus\s+de\s+d[eé]tails?|plus\s+d'infos?|en\s+savoir\s+plus)[\s!.?]*$",
]

def _is_followup_on_products(text: str) -> bool:
    t = text.lower().strip()
    for pattern in _FOLLOWUP_PATTERNS:
        if re.search(pattern, t):
            return True
    return False




_ORDINAL_MAP = {
    r'premi[eè]re?|numero\s*1|produit\s*1': 0,
    r'deuxi[eè]me?|numero\s*2|produit\s*2': 1,
    r'troisi[eè]me?|numero\s*3|produit\s*3': 2,
    r'quatri[eè]me?|numero\s*4|produit\s*4': 3,
    r'cinqui[eè]me?|numero\s*5|produit\s*5': 4,
}

def _find_targeted_product(text: str, products: list, last_recommended: dict = None) -> list:
    """
    Priorité :
    1. Nom ou référence explicite dans le texte
    2. Ordinal (premier, deuxième, numéro 3...)
    3. Pronom vague ("celle-là", "plus de details" seul, ...) -> last_recommended ou products[0]
    """
    t = text.lower()

    
    for p in products:
        m   = p.get("metadata", {})
        nom = m.get("nom", "").lower()
        pid = p.get("id", "").lower()
        if nom and nom in t:
            return [p]
        if pid and pid in t:
            return [p]
        words = [w for w in nom.split() if len(w) >= 4]
        if words and all(w in t for w in words):
            return [p]

    
    for pattern, idx in _ORDINAL_MAP.items():
        if re.search(pattern, t) and idx < len(products):
            return [products[idx]]

   
    pronom_vague = re.search(
        r"celui[- ]l[aà]|celle[- ]l[aà]|ce\s+produit|cette\s+chaudiere|"
        r"celle\s+que\s+tu\s+(m'as\s+)?conseill|ce\s+mod[eè]le|"
        r"^(donne[- ]moi\s+)?(plus\s+de\s+d[eé]tails?|plus\s+d'infos?|en\s+savoir\s+plus)[\s!.?]*$",
        t
    )
    if pronom_vague:
        if last_recommended:
            return [last_recommended]
        return [products[0]]

    return products




def _extract_recommended_product(llm_reply: str, products: list) -> dict | None:
    """
    Cherche dans la réponse LLM un nom de produit de la liste.
    Retourne le produit trouvé ou None.
    On prend le premier match (le bot ne recommande qu'un produit à la fois).
    """
    reply_lower = llm_reply.lower()
    for p in products:
        nom = p.get("metadata", {}).get("nom", "").lower()
        pid = p.get("id", "").lower()
        if nom and nom in reply_lower:
            return p
        if pid and pid in reply_lower:
            return p
        words = [w for w in nom.split() if len(w) >= 4]
        if words and sum(1 for w in words if w in reply_lower) >= max(1, len(words) - 1):
            return p
    return None




def _clean_query(text: str) -> str:
    t = text.lower()
    for noise in _QUERY_NOISE:
        t = t.replace(noise, " ")
    t = re.sub(r'\b[A-Z]{2,}[0-9]{2,}[A-Z0-9]*\b', '', t)
    t = re.sub(r'\bSKU-\w+\b', '', t, flags=re.IGNORECASE)
    return " ".join(t.split())


_CATEGORY_RAG_QUERY = {
    "chaudiere":     "chaudiere murale gaz condensation chauffage central",
    "climatisation": "climatiseur split reversible",
    "robinetterie":  "mitigeur robinet sanitaire",
    "visiophone":    "visiophone interphone portier video",
}

_OFF_TOPIC = {
    "chaudiere": [
        "friteuse", "four", "aspirateur", "congelateur", "refrigerateur",
        "micro-onde", "cafetiere", "mitigeur", "robinet",
        "visiophone", "interphone", "climatiseur", "split",
        "baignoire", "douche", "lavabo", "poignee", "porte",
        "rallonge de porte",
    ],
    "climatisation": [
        "friteuse", "four", "aspirateur", "chaudiere", "robinet",
        "mitigeur", "visiophone", "baignoire", "chauffe-eau",
    ],
    "robinetterie": [
        "friteuse", "four", "climatiseur", "chaudiere",
        "visiophone", "interphone", "baignoire",
    ],
    "visiophone": [
        "friteuse", "four", "climatiseur", "chaudiere",
        "robinet", "baignoire", "mitigeur",
    ],
}

_SPARE_PARTS_KEYWORDS = [
    "sonde", "echangeur de chaleur a plaques", "rallonge", "condensateur",
    "cache flamme", "pilote", "soupape", "vase d'expansion", "ventilateur",
    "bloc de gaz", "bruleur", "tube de sortie", "joint", "pressostat",
    "manometre", "thermistance", "electrovanne", "carte electronique",
    "circulateur", "pompe de circulation",
]

def _filter_products(products: list, category: str, want_complete_unit: bool = False) -> list:
    if not category or not products:
        return products
    noise_words = _OFF_TOPIC.get(category, [])
    clean = []
    for p in products:
        nom  = p.get("metadata", {}).get("nom", "").lower()
        text = (nom + " " + p.get("document_text", "")).lower()
        if any(n in text for n in noise_words):
            continue
        if want_complete_unit and category == "chaudiere":
            if any(kw in nom for kw in _SPARE_PARTS_KEYWORDS):
                continue
        clean.append(p)
    return clean


_SYSTEM_INJECTED_FIELDS = {"budget", "category", "sous_categorie"}

def _clean_memory(mem: dict) -> dict:
    return {k: v for k, v in mem.items() if k not in _SYSTEM_INJECTED_FIELDS}




class ChatManager:

    def __init__(self):
        self.history = ChatHistory()
        self.memory  = ConversationMemory()
        self.turns   = TurnManager()

        dialogues_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "docs", "dialogues_propres.json"
        ))
        loader = DialogueLoader(dialogues_path)
        self.dialogue_retriever = DialogueRetriever(loader.get_dialogues())

        chroma_client   = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        self.collection = chroma_client.get_collection(name=COLLECTION_NAME)
        self.model      = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        self.engine = BusinessRecommendationEngine()

        self.stable_category:   str  = ""
        self.last_products:     list = []
        self.last_rag_query:    str  = ""
        self.last_recommended:  dict = None

    def _resolve_category(self, user_message: str) -> str:
        from_msg = detect_category(user_message)
        if from_msg:
            self.stable_category = from_msg
            groq_session["current_category"] = from_msg
            return from_msg
        if self.stable_category:
            groq_session["current_category"] = self.stable_category
            return self.stable_category
        return ""

    def send_message(self, user_message: str) -> dict:

        normalized_message = _normalize_input(user_message)

        # 1. Historique et memoire
        self.history.add_user(user_message)
        extracted = MemoryExtractor.extract(normalized_message)
        if isinstance(extracted, dict):
            filtered_extracted = {
                k: v for k, v in extracted.items()
                if k not in _SYSTEM_INJECTED_FIELDS
            }
            self.memory.update(**filtered_extracted)

        self.turns.increment()
        turn_count = self.turns.get_turn_count()

       
        category = self._resolve_category(user_message)
        if not category:
            category = self._resolve_category(normalized_message)

       
        if _is_courtesy(user_message):
            filtered_products = []
            rag_query   = "[message de politesse]"
            is_followup = False

        
        elif is_vague_message(user_message) and not category:
            filtered_products = []
            rag_query   = "[message vague - pas de RAG]"
            is_followup = False

        else:
            is_followup   = _is_followup_on_products(user_message) and bool(self.last_products)
            is_mem_answer = _is_memory_answer(user_message) and bool(self.last_products)

            if is_followup or is_mem_answer:
                filtered_products = self.last_products

                if is_followup:
                    # FIX A : "plus de details" seul -> last_recommended
                    filtered_products = _find_targeted_product(
                        user_message, filtered_products, self.last_recommended
                    )

                rag_query   = "[contexte precedent conserve]"
                is_followup = True
            else:
                if category and category in _CATEGORY_RAG_QUERY:
                    rag_query = _CATEGORY_RAG_QUERY[category]
                    clean_msg = _clean_query(user_message)
                    useful_terms = [w for w in clean_msg.split()
                                    if len(w) > 3
                                    and w not in ("chauffage", "chaudiere", "veux", "cherche")]
                    if useful_terms:
                        rag_query = f"{rag_query} {' '.join(useful_terms[:2])}"
                else:
                    clean_msg = _clean_query(user_message)
                    rag_query = clean_msg or user_message

                self.last_rag_query = rag_query

                retrieved_products = retrieve(
                    query=rag_query,
                    chat_history=self.history.get_history(),
                    model=self.model,
                    collection=self.collection,
                    k=7,
                )

                filtered_products = _filter_products(
                    retrieved_products, category, want_complete_unit=True,
                )
                if not filtered_products:
                    filtered_products = _filter_products(
                        retrieved_products, category, want_complete_unit=False
                    )

        mem = _clean_memory(self.memory.to_dict())

        business_result = self.engine.process_business_rules(
            category=category,
            collected_information=mem,
            turn_count=turn_count,
            retrieved_products=filtered_products,
            user_question=user_message,
        )

        if filtered_products and not business_result.get("products"):
            business_result["products"] = filtered_products

        business_result["allow_recommendation"]  = True
        business_result["collected_information"]  = mem
        business_result["is_followup"]            = is_followup
        
        business_result["last_recommended"]       = self.last_recommended
       
        business_result["is_courtesy"]            = _is_courtesy(user_message)

        llm_reply = generate_answer(user_message, business_result)
        self.history.add_assistant(llm_reply)

       
        all_products_pool = self.last_products or filtered_products
        if all_products_pool:
            detected = _extract_recommended_product(llm_reply, all_products_pool)
            if detected:
                self.last_recommended = detected

        
        if filtered_products:
            if not (is_followup and len(filtered_products) == 1 and len(self.last_products) > 1):
                self.last_products = filtered_products

        return {
            "user_message":         user_message,
            "memory":               mem,
            "turn_count":           turn_count,
            "retrieval_query":      rag_query,
            "chat_history":         self.history.get_history(),
            "retrieved_products":   filtered_products,
            "business_status":      business_result.get("status", ""),
            "allow_recommendation": True,
            "llm_answer":           llm_reply,
            "missing_information":  business_result.get("missing_information", []),
            "category":             category,
            "is_followup":          is_followup,
        }

    def reset(self):
        self.history          = ChatHistory()
        self.memory           = ConversationMemory()
        self.turns            = TurnManager()
        self.stable_category  = ""
        self.last_products    = []
        self.last_rag_query   = ""
        self.last_recommended = None
        groq_reset()