import pandas as pd
import os

def prepare_product_documents(csv_path: str):
    """
    Reads the raw product catalog CSV using the exact Energical column schema,
    formatting comprehensive strings for RAG and keeping keys for business rules.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Catalogue file not found at: {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # Handle missing values based on your schema data types
    df = df.fillna({
        'nom_produit': 'Produit sans nom',
        'categorie': 'Général',
        'sous_categorie': 'Général',
        'description_courte': 'Aucune spécification technique disponible.',
        'prix_da': '0',
        'statut_stock': 'Rupture',
        'produit_alternatif_id': 'Aucun'
    })
    
    documents = []
    metadatas = []
    ids = []
    
    for index, row in df.iterrows():
        # Get the real product ID from 'id_produit' column
        prod_id = str(row['id_produit'])
        
        # CREATE THE SEAMLESS TEXT STRING (What the Vector model reads)
        # We include the sub-category and short description to give the vector more meaning
        text_string = (
            f"Produit: {row['nom_produit']} | "
            f"Catégorie: {row['categorie']} ({row['sous_categorie']}) | "
            f"Description: {row['description_courte']} | "
            f"Prix: {row['prix_da']} DA"
        )
        
        # CREATE THE METADATA DICTIONARY (What Programmer 2 reads)
        # Note the exact names match CSV columns
        metadata = {
            "id": prod_id,
            "nom": str(row['nom_produit']),
            "categorie": str(row['categorie']),
            "prix": str(row['prix_da']),
            "statut_stock": str(row['statut_stock']),
            "id_produit_alternatif": str(row['produit_alternatif_id'])
        }
        
        documents.append(text_string)
        metadatas.append(metadata)
        ids.append(prod_id)
        
    print(f"[document_loader] Successfully parsed {len(documents)} products from CSV.")
    return documents, metadatas, ids

if __name__ == "__main__":
    TEST_CSV_PATH = "../docs/catalogue_propre.csv"
    try:
        docs, metas, p_ids = prepare_product_documents(TEST_CSV_PATH)
        print("\n=== Data Schema Verification ===")
        print(f"TEXT FORMAT EXAMPLE:\n{docs[0]}\n")
        print(f"METADATA CONTRACT EXAMPLE:\n{metas[0]}")
    except Exception as e:
        print(f"Mapping Error: {e}")