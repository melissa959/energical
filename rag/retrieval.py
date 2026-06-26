import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"

def retrieve(query: str, model: SentenceTransformer, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """
    Step 4 / Final Contract: Takes a raw user query, embeds it, matches it 
    against the vector database, and returns the top k products with their metadata.
    """
    # 1. Convert the real-time user query into a vector coordinate
    query_vector = model.encode(query).tolist()
    
    # 2. Query ChromaDB for the closest mathematical matches
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k
    )
    
    # 3. Format the results into a clean, structured list of dictionaries for your team
    formatted_results = []
    
    # ChromaDB returns nested lists, so we loop through the first query's results
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            product_packet = {
                "id": results['ids'][0][i],
                "document_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            }
            formatted_results.append(product_packet)
            
    return formatted_results

if __name__ == "__main__":
    # --- Local Standalone Test Running Engine ---
    print("[retrieval] Initializing persistent database connection...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    print("[retrieval] Loading embedding engine...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Test with a messy Algerian Darija mix query!
    TEST_QUERY = "bghit chaudière khfifa dial gaz"
    print(f"\n Testing Live Retrieval Engine for Query: '{TEST_QUERY}'")
    
    top_matches = retrieve(TEST_QUERY, model, collection, k=3)
    
    print("\n=== LIVE RETRIEVAL RESULTS (TOP 3 MATCHES) ===")
    for idx, item in enumerate(top_matches, 1):
        print(f"\nMatch #{idx} (Distance Score: {item['distance']:.4f})")
        print(f" ├── Text String sent to LLM: {item['document_text']}")
        print(f" └── Metadata sent to Programmer 2: Stock -> {item['metadata']['statut_stock']} | Alt ID -> {item['metadata']['id_produit_alternatif']}")