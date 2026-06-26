import chromadb

# 1. Connect to your local database folder
client = chromadb.PersistentClient(path="../chroma_db")
collection = client.get_collection(name="energical_catalog")

# 2. Grab exactly ONE record out of the database raw storage
raw_data = collection.get(limit=1)

# 3. Print it to your terminal to inspect the keys
print(" YOUR REALS DATA STRUCTURE:")
print(raw_data)