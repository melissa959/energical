import chromadb
from sentence_transformers import SentenceTransformer
import ollama  # Handles the context-condensing LLM call
# Import the class from your separate intent_matcher.py file!
from intent_matcher import ScalableIntentMatcher 

CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"

# Initialize the scalable matcher globally (reads/creates 'patterns_catalog.json')
matcher = ScalableIntentMatcher()

def contextualize_query(user_query: str, chat_history: list) -> str:
    """
    Reads the history to turn shorthand statements (e.g., "اعطيني وحدة خفيفة")
    into an explicit search query based on what was discussed before.
    """
    if not chat_history:
        return user_query
        
    # Take the last 3 turns to keep context brief and fast
    recent_history = chat_history[-3:]
    history_str = ""
    for turn in recent_history:
        history_str += f"{turn['role'].upper()}: {turn['content']}\n"
        
    condensing_prompt = f"""
    Given the following conversation history and a follow-up question, rewrite the follow-up question to be a standalone search query containing explicit hardware keywords (like boiler, gas, electric).
    
    Chat History:
    {history_str}
    Follow-up Question: {user_query}
    
    Standalone search query (Output ONLY the optimized search string, nothing else):
    """
    try:
        response = ollama.generate(model='llama3', prompt=condensing_prompt)
        return response['response'].strip()
    except Exception:
        # Fallback to the original query if Ollama is busy or offline
        return user_query

def retrieve(query: str, chat_history: list, model: SentenceTransformer, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """
    Upgraded Phase 3 Retrieval Engine:
    Takes the query and chat history from Programmer 1, extracts multilingual 
    patterns, searches ChromaDB, and passes the output to Programmer 2.
    """
    # 1. READ AND PROCESS THE MEMORY CONVERSATION HERE
    optimized_query = contextualize_query(query, chat_history)
    
    # 2. Extract dynamic keywords using your new modular file
    extracted_keywords = matcher.extract_keywords(optimized_query)
    
    # Combine the original text and matching tokens to maximize mathematical distance accuracy
    final_search_string = f"{optimized_query} {extracted_keywords}".strip()
    
    # 3. Convert the enriched search anchor into a vector coordinate
    query_vector = model.encode(final_search_string).tolist()
    
    # 4. Query ChromaDB for the closest mathematical matches
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k
    )
    
    # 5. Format the results into a structured list of dictionaries
    formatted_results = []
    
    # Your verified nested loop parsing ChromaDB's output arrays
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            product_packet = {
                "id": results['ids'][0][i],
                "document_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "search_anchor_used": final_search_string  # Helpful trail for your team to debug matches
            }
            formatted_results.append(product_packet)
            
    return formatted_results

if __name__ == "__main__":
    # --- Local Standalone Verification Engine ---
    print("[RAG Backend] Connecting to ChromaDB storage directory...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    print("[RAG Backend] Loading multilingual transformer weights...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Mocking data structures provided by Programmer 1's UI layer
    MOCK_HISTORY = [
        {"role": "user", "content": "bghit chaudière dial gaz"},
        {"role": "assistant", "content": "Bien sûr! Quel budget ou spécification recherchez-vous?"}
    ]
    TEST_INPUT = "اعطيني وحدة خفيفة" # "Give me a lightweight one"
    
    print(f"\n[Test] Simulating integration request with query: '{TEST_INPUT}'")
    matches = retrieve(TEST_INPUT, MOCK_HISTORY, model, collection, k=2)
    
    print("\n=== SYSTEM INTEGRATION OUTPUT ===")
    for idx, item in enumerate(matches, 1):
        print(f"\nMatch #{idx} (Distance: {item['distance']:.4f})")
        print(f" ├── Enriched Anchor: {item['search_anchor_used']}")
        print(f" ├── Extracted Content: {item['document_text']}")
        print(f" └── Target Metadata: Stock State -> {item['metadata']['statut_stock']}")