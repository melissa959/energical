from stock_interceptor import StockInterceptor

interceptor = StockInterceptor()

retrieved_products = [
    {
        "id": "P042",
        "document_text": "Old product",

        "metadata": {
            "nom": "Chaudière Standard",
            "prix": 120000,
            "categorie": "Chaudière",
            "statut_stock": "Rupture",
            "id_produit_alternatif": "P089"
        }
    }
]

result = interceptor.replace_if_needed(retrieved_products)

print(result)

