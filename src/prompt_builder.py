from typing import List, Dict
import os


class PromptBuilder:

    @staticmethod
    def load_system_prompt() -> str:
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            "..", "prompts", "system_prompt.txt"
        ))
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def build(
        memory: dict,
        turn_count: int,
        chat_history: List[Dict],
        products: list,
        user_message: str
    ) -> list:

        messages = []

      
        system_prompt = PromptBuilder.load_system_prompt()
        system_prompt = system_prompt.replace(
            "{{ turn_count }}", str(turn_count)
        )
        system_prompt = system_prompt.replace(
            "{{ memory }}", str(memory)
        )

        messages.append({
            "role": "system",
            "content": system_prompt
        })

      
        if products:
            context = "## Retrieved Products\n\n"
            for i, p in enumerate(products, 1):
                meta = p.get("metadata", {})
                context += (
                    f"Product {i}:\n"
                    f"- Name: {meta.get('nom', 'N/A')}\n"
                    f"- Category: {meta.get('categorie', 'N/A')}\n"
                    f"- Price: {meta.get('prix', 'N/A')} DA\n"
                    f"- Stock: {meta.get('statut_stock', 'N/A')}\n"
                    f"- Alternative ID: {meta.get('id_produit_alternatif', 'None')}\n\n"
                )
        else:
            context = "## Retrieved Products\nNo products found for this query.\n"

        messages.append({
            "role": "system",
            "content": context
        })

       
        if chat_history:
            messages.extend(chat_history)

      
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages