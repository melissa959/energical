from business.process_business_rules import BusinessRecommendationEngine

engine = BusinessRecommendationEngine()


retrieved_products = [
    {
        "id": "P001",
        "document_text": "Filtre à gaz pour chaudière à connexion G1/2M - G3/4F",
        "metadata": {
            "nom": "Filtre à gaz G1/2M - G3/4F",
            "categorie": "Électroménager",
            "prix": 1300.0,
            "statut_stock": "Disponible",
            "id_produit_alternatif": ""
        }
    },
    {
        "id": "P002",
        "document_text": "Chaudière SL-DL32 idéale pour chauffage résidentiel",
        "metadata": {
            "nom": "Chaudière SL-DL32",
            "categorie": "Électroménager",
            "prix": 131000.0,
            "statut_stock": "Disponible",
            "id_produit_alternatif": ""
        }
    },
]

user_question = "Bonjour, je cherche une chaudière pour ma maison."

result = engine.process_business_rules(
    category="chaudiere",
    collected_information={
    "surface_m2": 120,
    "region": "Nord",
    "condensation": "oui",
    "energie": "gaz",     
    "usage": "chauffage"  
},
    turn_count=3,          
    retrieved_products=retrieved_products,
    user_question=user_question  
)

print("STATUS :", result["status"])
print("ALLOW  :", result["allow_recommendation"])
print("\n--- LLM ANSWER ---\n")
print(result["llm_answer"])