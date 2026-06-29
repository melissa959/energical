import chromadb


client = chromadb.PersistentClient(path="../chroma_db")
collection = client.get_collection(name="energical_catalog")


raw_data = collection.get(limit=1)


print(" YOUR REALS DATA STRUCTURE:")
print(raw_data)