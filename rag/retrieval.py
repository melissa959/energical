import chromadb
from sentence_transformers import SentenceTransformer
# Import the class from your separate intent_matcher.py file!
from intent_matcher import ScalableIntentMatcher 

CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"

# Initialize the scalable matcher globally (reads/creates 'patterns_catalog.json')
matcher = ScalableIntentMatcher()

def retrieve(query: str, chat_history: list, model: SentenceTransformer, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """
    PHASE 3 RETRIEVAL ENGINE (Corrected Contract)
    
    Inputs:
      - query: The raw current user string.
      - chat_history: Accepted to maintain pipeline structure (passed to metadata or logged).
    """
    
    # 1. Extract dynamic keywords directly from the user's raw query text
    extracted_keywords = matcher.extract_keywords(query)
    
    # 2. Combine the original text and matching tokens to maximize mathematical alignment
    final_search_string = f"{query} {extracted_keywords}".strip()
    
    # 3. Convert the enriched search anchor into a vector coordinate
    query_vector = model.encode(final_search_string).tolist()
    
    # 4. Query ChromaDB for the closest mathematical matches
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k
    )
    
    # 5. Format the results into a structured list of dictionaries
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
            
    # Send these raw products directly to Programmer 2 (Phase 4B)
    return formatted_results

if __name__ == "__main__":
    # --- Local Standalone Verification Engine ---
    print("[RAG Backend] Connecting to ChromaDB storage directory...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    print("[RAG Backend] Loading multilingual transformer weights...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Simulating what Programmer 1 passes. Your code safely accepts it without crashing.
    MOCK_HISTORY = [{"role": "user", "content": "Hello"}]
    TEST_INPUT = "bghit chaudière khfifa dial gaz svpl"
    
    matches = retrieve(TEST_INPUT, MOCK_HISTORY, model, collection, k=2)
    
    print("\n=== CLEAN PHASE 3 RETRIEVAL OUTPUT ===")
    for idx, item in enumerate(matches, 1):
        print(f"\nMatch #{idx} (Distance: {item['distance']:.4f})")
        print(f" ├── Enriched Anchor: {item['search_anchor_used']}")
        print(f" └── Target Metadata: Stock State -> {item['metadata']['statut_stock']}")