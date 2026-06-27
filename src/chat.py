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
from rag.retrieval import retrieve


CHROMA_DATA_PATH = "chroma_db"
COLLECTION_NAME = "energical_catalog"


class ChatManager:

    def __init__(self):

        # Part 1 components
        self.history = ChatHistory()
        self.memory = ConversationMemory()
        self.turns = TurnManager()

        dialogues_path = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "docs", "dialogues_propres.json"
))
        loader = DialogueLoader(dialogues_path)
        self.dialogue_retriever = DialogueRetriever(loader.get_dialogues())
        self.query_builder = QueryBuilder()

        # Phase 3 components
        print("[ChatManager] Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        self.collection = client.get_collection(name=COLLECTION_NAME)

        print("[ChatManager] Loading embedding model...")
        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )

    def send_message(self, user_message: str) -> dict:

        # Task 1 — receive message
        # Task 2 — add to chat history
        self.history.add_user(user_message)

        # Task 3 — extract structured info
        extracted = MemoryExtractor.extract(user_message)

        # Task 4 — update memory
        self.memory.update(**extracted)

        # Task 5 — increment turn counter
        self.turns.increment()

        # Build RAG query
        dialogue_result = self.dialogue_retriever.retrieve(user_message)
        query = self.query_builder.build_query(
            user_message=user_message,
            memory=self.memory,
            dialogue_result=dialogue_result,
        )

        # Phase 3 — retrieve products from ChromaDB
        retrieved_products = retrieve(
            query=query,
            chat_history=self.history.get_history(),
            model=self.model,
            collection=self.collection,
            k=5
        )

        return {
            "user_message":       user_message,
            "memory":             self.memory.to_dict(),
            "turn_count":         self.turns.get_turn_count(),
            "dialogue":           dialogue_result,
            "retrieval_query":    query,
            "chat_history":       self.history.get_history(),
            "retrieved_products": retrieved_products,  # Phase 3 output
        }