from business.process_business_rules import BusinessRecommendationEngine

engine = BusinessRecommendationEngine()

retrieved_products = [
    {
        "id": "P042",

        "document_text": "Chaudière",

        "metadata": {
            "nom": "Chaudière Standard",
            "prix": 120000,
            "categorie": "Chaudière",
            "statut_stock": "Disponible",
            "id_produit_alternatif": "P089"
        }
    }
]

user_information = {

    "usage": "Maison",

    "surface_m2": 150,

    "energie": "Gaz",

    "condensation": True,

    "region": "Alger"

}

result = engine.process_business_rules(

    category="chaudiere",

    collected_information=user_information,

    turn_count=3,

    retrieved_products=retrieved_products

)

print(result)