import pandas as pd
df = pd.read_csv(r"C:\Users\SAN\Documents\GitHub\energical\docs\catalogue_propre.csv")
print("categories:", df["categorie"].unique().tolist())
print("sous_categories:", df["sous_categorie"].unique().tolist())