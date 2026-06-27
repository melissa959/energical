class QueryBuilder:

    def build_query(self, user_message: str, memory, dialogue_result) -> str:

        query_parts = []

        # 1. Category family from dialogue match
        if dialogue_result and dialogue_result.get("family"):
            query_parts.append(dialogue_result["family"])

        # 2. Products cited in matched dialogue
        if dialogue_result and dialogue_result.get("products"):
            for p in dialogue_result["products"]:
                query_parts.append(p)

        # 3. Structured memory fields
        if memory.category:
            query_parts.append(memory.category)

        if memory.sous_categorie:
            query_parts.append(memory.sous_categorie)

        if memory.capacity:
            query_parts.append(f"{memory.capacity} litres")

        # 4. Raw user message (semantic nuance)
        query_parts.append(user_message)

        return " ".join(query_parts).strip()