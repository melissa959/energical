import chromadb
from sentence_transformers import SentenceTransformer
from intent_matcher import ScalableIntentMatcher 

CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"


matcher = ScalableIntentMatcher()

def retrieve(query: str, chat_history: list, model: SentenceTransformer, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """
    PHASE 3 RETRIEVAL ENGINE (Corrected Contract)
    
    Inputs:
      - query: The raw current user string.
      - chat_history: Accepted to maintain pipeline structure (passed to metadata or logged).
    """
    
    
    extracted_keywords = matcher.extract_keywords(query)
    
    
    final_search_string = f"{query} {extracted_keywords}".strip()
    
   
    query_vector = model.encode(final_search_string).tolist()
    
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k
    )
    
    
    formatted_results = []
    
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            product_packet = {
                "id": results['ids'][0][i],
                "document_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "search_anchor_used": final_search_string
            }
            formatted_results.append(product_packet)
            
    
    return formatted_results

if __name__ == "__main__":
   
    print("[RAG Backend] Connecting to ChromaDB storage directory...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    print("[RAG Backend] Loading multilingual transformer weights...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    
    MOCK_HISTORY = [{"role": "user", "content": "Hello"}]
    TEST_INPUT = "bghit chaudière khfifa dial gaz svpl"
    
    matches = retrieve(TEST_INPUT, MOCK_HISTORY, model, collection, k=2)
    
    print("\n=== CLEAN PHASE 3 RETRIEVAL OUTPUT ===")
    for idx, item in enumerate(matches, 1):
        print(f"\nMatch #{idx} (Distance: {item['distance']:.4f})")
        print(f" ├── Enriched Anchor: {item['search_anchor_used']}")
        print(f" └── Target Metadata: Stock State -> {item['metadata']['statut_stock']}")