import sys
import os

# Ensure system paths remain bulletproof across different folders
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

# Import your Phase 3 module!
from rag.retrieval import retrieve

# FIX: Normalize path so Streamlit can locate your generated vector folder
CHROMA_DATA_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
COLLECTION_NAME = "energical_catalog"


class ChatManager:

    def __init__(self):
        # Phase 4A components
        self.history = ChatHistory()
        self.memory = ConversationMemory()
        self.turns = TurnManager()

        dialogues_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "docs", "dialogues_propres.json"
        ))
        loader = DialogueLoader(dialogues_path)
        self.dialogue_retriever = DialogueRetriever(loader.get_dialogues())
        self.query_builder = QueryBuilder()

        # Phase 3 components
        print(f"[ChatManager] Safely connecting to data cluster at: {CHROMA_DATA_PATH}")
        client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        self.collection = client.get_collection(name=COLLECTION_NAME)

        print("[ChatManager] Loading shared translation vector embedding core...")
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def send_message(self, user_message: str) -> dict:
        # --- PHASE 4A — PART 1: CONVERSATION PIPELINE ---
        # Task 2 — add to chat history
        self.history.add_user(user_message)

        # Task 3 — extract structured info
        extracted = MemoryExtractor.extract(user_message)

        # Task 4 — update memory (safely handle dictionary extraction arrays)
        if isinstance(extracted, dict):
            self.memory.update(**extracted)

        # Task 5 — increment turn counter
        self.turns.increment()

        # Build Retrieval Query (Current message + Conversation Memory metadata tags)
        dialogue_result = self.dialogue_retriever.retrieve(user_message)
        query = self.query_builder.build_query(
            user_message=user_message,
            memory=self.memory,
            dialogue_result=dialogue_result,
        )

        # --- PHASE 3 — RAG RETRIEVAL PIPELINE (YOUR PART) ---
        # Convert query into embedding, search ChromaDB, retrieve documents & metadata
        retrieved_products = retrieve(
            query=query,
            chat_history=self.history.get_history(),
            model=self.model,
            collection=self.collection,
            k=5
        )

        # Return the clean merged state contract directly to the UI
        return {
            "user_message":       user_message,
            "memory":             self.memory.to_dict(),
            "turn_count":         self.turns.get_turn_count(),
            "dialogue":           dialogue_result,
            "retrieval_query":    query,
            "chat_history":       self.history.get_history(),
            "retrieved_products": retrieved_products,  # The verified vector search output array
        }