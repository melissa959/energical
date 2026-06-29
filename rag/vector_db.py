import os
import chromadb
from sentence_transformers import SentenceTransformer
from document_loader import prepare_product_documents
from intent_matcher import ScalableIntentMatcher

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "docs" / "catalogue_propre.csv"
CHROMA_DATA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "energical_catalog"

def build_vector_database():
    print("[Database Builder] Extracting data from product catalog CSV...")
  
    documents, metadatas, ids = prepare_product_documents(CSV_PATH)
    
    
    print("[Database Builder] Initializing new physical ChromaDB instance...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
   
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(name=COLLECTION_NAME,
                                          metadata={"hnsw:space": "cosine"}) # to normalize
    
    
    print("[Database Builder] Loading translation embedding engine weights...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    
    matcher = ScalableIntentMatcher()
    
    enriched_documents = []
    print("[Database Builder] Optimizing semantic descriptions with keyword maps...")
    for doc in documents:
        keywords = matcher.extract_keywords(doc)
       
        final_text = f"{doc} {keywords}".strip()
        enriched_documents.append(final_text)
        
   
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