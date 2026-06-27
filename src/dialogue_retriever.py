import numpy as np
from sentence_transformers import SentenceTransformer


class DialogueRetriever:

    def __init__(self, dialogues):

        self.dialogues = dialogues
        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.client_messages = []
        self.dialogue_index = []
        self.embeddings = None

        self._build_index()
        self._build_embeddings()

    def _build_index(self):

        self.client_messages = []
        self.dialogue_index = []

        for dialogue in self.dialogues:

            if not isinstance(dialogue, dict):
                continue

            tours = dialogue.get("tours", [])

            if not isinstance(tours, list):
                continue

            for i, turn in enumerate(tours):

                if not isinstance(turn, dict):
                    continue

                if turn.get("role") != "client":
                    continue

                msg = turn.get("msg")

                if not isinstance(msg, str):
                    continue

                msg = msg.strip()

                if msg == "":
                    continue

                self.client_messages.append(msg)
                self.dialogue_index.append({
                    "dialogue": dialogue,
                    "turn_index": i
                })

        print(f"[DialogueRetriever] Loaded {len(self.client_messages)} client messages")

    def _build_embeddings(self):

        if len(self.client_messages) == 0:
            raise ValueError(
                "DialogueRetriever ERROR: No valid client messages found. "
                "Check your JSON structure."
            )

        self.embeddings = self.model.encode(self.client_messages)
        print(f"[DialogueRetriever] Built embeddings: {len(self.embeddings)} vectors")

    def retrieve(self, query: str):

        query_embedding = self.model.encode(query)

        if self.embeddings is None or len(self.embeddings) == 0:
            return None

        similarities = np.dot(
            self.embeddings,
            query_embedding
        ) / (
            np.linalg.norm(self.embeddings, axis=1) *
            np.linalg.norm(query_embedding)
        )

        best_idx = int(np.argmax(similarities))
        matched = self.dialogue_index[best_idx]["dialogue"]

        return {
            "id":       matched.get("id"),
            "family":   matched.get("famille_cible"),
            "language": matched.get("langue"),
            "products": matched.get("produits_cites"),
            "score":    float(similarities[best_idx])
        }