# ==========================================================
# stock_interceptor.py
#
# Phase 4B - Business Recommendation Engine
#
# This module verifies whether retrieved products can be
# recommended according to Energical's stock policy.
#
# Responsibilities:
#   - Keep available products.
#   - Replace unavailable products.
#   - Detect missing alternatives.
#   - Never let the LLM recommend unavailable products.
# ==========================================================

import os
import pandas as pd


class StockInterceptor:

    def __init__(self):

        # --------------------------------------------------
        # Load Energical product catalog
        # --------------------------------------------------

        current_dir = os.path.dirname(os.path.abspath(__file__))

        csv_path = os.path.join(
            current_dir,
            "..",
            "docs",
            "energical_catalogue_produits.csv"
        )

        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"Catalog not found:\n{csv_path}"
            )

        self.catalog = pd.read_csv(csv_path)

        # Dictionary:
        # key = id_produit
        # value = complete product row

        self.products = {}

        for _, row in self.catalog.iterrows():

            self.products[str(row["id_produit"])] = row

    # ------------------------------------------------------
    # Main Business Rule
    # ------------------------------------------------------

    def replace_if_needed(self, retrieved_products):

        validated_products = []

        # Nothing returned by RAG
        if not retrieved_products:
            return validated_products

        for product in retrieved_products:

            # ----------------------------------------------
            # Validate product format
            # ----------------------------------------------

            metadata = product.get("metadata")

            if metadata is None:

                validated_products.append({

                    "status": "INVALID_PRODUCT",

                    "message":
                        "Product metadata is missing.",

                    "original_product": product

                })

                continue

            # ----------------------------------------------
            # Product available
            # ----------------------------------------------

            stock = metadata.get("statut_stock", "Rupture")

            if stock != "Rupture":

                product["status"] = "AVAILABLE"

                validated_products.append(product)

                continue

            # ----------------------------------------------
            # Product unavailable
            # ----------------------------------------------

            alternative_id = metadata.get(
                "id_produit_alternatif"
            )

            # No alternative defined

            if (
                alternative_id is None
                or str(alternative_id).strip() == ""
                or str(alternative_id).lower() == "aucun"
                or alternative_id not in self.products
            ):

                validated_products.append({

                    "status": "NO_ALTERNATIVE",

                    "message":
                        "This product is out of stock and no replacement product exists.",

                    "original_product": product

                })

                continue

            # ----------------------------------------------
            # Load replacement product
            # ----------------------------------------------

            alt = self.products[str(alternative_id)]

            replacement = {

                "status": "REPLACED",

                "message":
                    "Original product unavailable. Replacement selected automatically.",

                "id": str(alt["id_produit"]),

                "document_text":
                    f"Produit: {alt['nom_produit']} | "
                    f"Catégorie: {alt['categorie']} "
                    f"({alt['sous_categorie']}) | "
                    f"Description: {alt['description_courte']} | "
                    f"Prix: {alt['prix_da']} DA",

                "metadata": {

                    "nom":
                        alt["nom_produit"],

                    "prix":
                        alt["prix_da"],

                    "categorie":
                        alt["categorie"],

                    "statut_stock":
                        alt["statut_stock"],

                    "id_produit_alternatif":
                        alt["produit_alternatif_id"]

                }

            }

            validated_products.append(replacement)

        return validated_products