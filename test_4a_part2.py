from src.prompt_builder import PromptBuilder
from src.llm_loader import LLMLoader

fake_products = [
    {
        "metadata": {
            "nom": "Chaudière SL-DL32",
            "categorie": "Électroménager",
            "prix": "131000",
            "statut_stock": "Disponible",
            "id_produit_alternatif": "None"
        }
    }
]

fake_memory = {
    "category": "Électroménager",
    "sous_categorie": "Chauffage et régulation gaz",
    "budget": 80000,
    "capacity": None
}

messages = PromptBuilder.build(
    memory=fake_memory,
    turn_count=3,
    chat_history=[
        {"role": "user", "content": "bonjour"},
        {"role": "assistant", "content": "Bonjour ! Que cherchez-vous ?"},
        {"role": "user", "content": "bghit chaudière dial gaz"}
    ],
    products=fake_products,
    user_message="mon budget c'est 80000 DA"
)

llm = LLMLoader()
response = llm.generate(messages)

print("=== FULL PART 2 TEST ===")
print(response)