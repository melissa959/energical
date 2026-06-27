import os
import chromadb
from sentence_transformers import SentenceTransformer
# Import your two critical helper files
from document_loader import prepare_product_documents
from intent_matcher import ScalableIntentMatcher

CSV_PATH = "../docs/catalogue_propre.csv"
CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"

def build_vector_database():
    print("[Database Builder] Extracting data from product catalog CSV...")
    # 1. Read and format items from CSV using your document loader
    documents, metadatas, ids = prepare_product_documents(CSV_PATH)
    
    # 2. Connect to ChromaDB (It will automatically create the folder since it's deleted)
    print("[Database Builder] Initializing new physical ChromaDB instance...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
    # Delete the collection if it exists as an empty remnant, then create a fresh one
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(name=COLLECTION_NAME,
                                          metadata={"hnsw:space": "cosine"}) # to normalize
    
    # 3. Load your embedding model
    print("[Database Builder] Loading translation embedding engine weights...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 4. Use your Scalable Matcher to enrich the database descriptions with keyword anchors
    matcher = ScalableIntentMatcher()
    
    enriched_documents = []
    print("[Database Builder] Optimizing semantic descriptions with keyword maps...")
    for doc in documents:
        # Extract keywords relevant to this specific product text string
        keywords = matcher.extract_keywords(doc)
        # Create an enriched description string containing both the product data and matching keywords
        final_text = f"{doc} {keywords}".strip()
        enriched_documents.append(final_text)
        
    # 5. Generate embeddings and save directly into your clean directory
    print(f"[Database Builder] Computing vector grids for {len(enriched_documents)} products. Please wait...")
    embeddings = model.encode(enriched_documents, show_progress_bar=True).tolist()
    
    collection.add(
        embeddings=embeddings,
        documents=enriched_documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("\n SUCCESS: New chroma_db created and fully loaded with optimized arrays!")

if __name__ == "__main__":
    build_vector_database()