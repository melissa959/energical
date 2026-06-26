from sentence_transformers import SentenceTransformer
import numpy as np

def calculate_similarity(vector1, vector2):
    """Calculates how close two vectors are in mathematical space."""
    dot_product = np.dot(vector1, vector2)
    norm_v1 = np.linalg.norm(vector1)
    norm_v2 = np.linalg.norm(vector2)
    return dot_product / (norm_v1 * norm_v2)

def verify_embeddings():
    # 1. Load the multilingual model locally
    print("[embeddings] Loading paraphrase-multilingual-MiniLM-L12-v2...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 2. Define our test cases (Darija vs Official French Catalog Text)
    customer_query = "bghit chaudière dial gaz" 
    catalog_product = "Produit: Chaudière murale gaz 24kW | Catégorie: Chauffage"
    wrong_product   = "Produit: Mitigeur lavabo chromé | Catégorie: Robinetterie"
    
    # 3. Convert sentences into mathematical vectors
    print("[embeddings] Encoding sentences into vectors...")
    query_vector   = model.encode(customer_query)
    match_vector   = model.encode(catalog_product)
    wrong_vector   = model.encode(wrong_product)
    
    # 4. Calculate similarity scores (Value between 0 and 1)
    good_score  = calculate_similarity(query_vector, match_vector)
    wrong_score = calculate_similarity(query_vector, wrong_vector)
    
    print("\n=== EMBEDDING VERIFICATION RESULTS ===")
    print(f"User Query: '{customer_query}'")
    print(f"-> Similarity to CORRECT product (Boiler): {good_score:.3f}")
    print(f"-> Similarity to WRONG product (Faucet):  {wrong_score:.3f}")
    
    # 5. Asset protection validation check
    if good_score > 0.70:
        print("\n SUCCESS: The model understands Algerian Darija mapping to French!")
    else:
        print("\n WARNING: Embedding match threshold is too low.")

if __name__ == "__main__":
    verify_embeddings()