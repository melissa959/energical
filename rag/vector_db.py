import os
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
# Import your document loader logic directly from your Step 1 file
from document_loader import prepare_product_documents

CHROMA_DATA_PATH = "../chroma_db"
COLLECTION_NAME = "energical_catalog"

def build_vector_index(csv_path: str, model: SentenceTransformer):
    """
    Step 3: Processes all 731 rows from the catalog, computes their embeddings,
    and stores them in a local, persistent ChromaDB collection.
    """
    print("\n===  BUILDING VECTOR DATABASE INDEX ===")
    
    # 1. Fetch data from Step 1
    documents, metadatas, ids = prepare_product_documents(csv_path)
    
    # 2. Connect to a local storage client
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    
    # 3. Generate embeddings for all documents at once
    print(f"[vector_db] Encoding {len(documents)} text blocks into mathematical vectors...")
    embeddings = model.encode(documents, show_progress_bar=True)
    
    # Convert numpy vectors to regular lists for ChromaDB compatibility
    embeddings_list = [emb.tolist() for emb in embeddings]
    
    # 4. Insert everything into ChromaDB in controlled batches of 100
    batch_size = 100
    print("[vector_db] Loading database records...")
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        
        collection.add(
            ids=ids[i:end_idx],
            embeddings=embeddings_list[i:end_idx],
            metadatas=metadatas[i:end_idx],
            documents=documents[i:end_idx]
        )
        print(f" └── Loaded entries {i} through {end_idx} successfully.")
        
    print(f"\n SUCCESS: Vector index built. 731 items written to '{CHROMA_DATA_PATH}/'")
    return collection

if __name__ == "__main__":
    # Path to your catalog data
    CSV_FILE_PATH = "../docs/energical_catalogue_produits.csv"
    
    # Initialize the model we verified in Step 2
    print("[vector_db] Attaching local embedding engine...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Run the database indexing pipeline
    build_vector_index(CSV_FILE_PATH, model)