class QueryBuilder:

    def build_query(self, user_message: str, memory, dialogue_result) -> str:

        query_parts = []

       
        if dialogue_result and dialogue_result.get("family"):
            query_parts.append(dialogue_result["family"])

      
        if dialogue_result and dialogue_result.get("products"):
            for p in dialogue_result["products"]:
                query_parts.append(p)

       
        if memory.category:
            query_parts.append(memory.category)

        if memory.sous_categorie:
            query_parts.append(memory.sous_categorie)

        if memory.capacity:
            query_parts.append(f"{memory.capacity} litres")

       
        query_parts.append(user_message)

        return " ".join(query_parts).strip()