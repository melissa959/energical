# ==========================================================
# process_business_rules.py
#
# Phase 4B - Business Recommendation Engine
#
# Receives products from the RAG, applies all business rules,
# then sends the validated products to the LLM.
# ==========================================================

from .decision_tree import DecisionTree
from .stock_interceptor import StockInterceptor
from .guardrails import Guardrails

from llm.groq_client import generate_answer


def _send_to_llm(user_question: str, business_result: dict) -> dict:
    """
    Safety wrapper:
    - Ensures 'products' key always exists before calling the LLM
    - Calls generate_answer and stores the reply
    - Returns the enriched business_result
    """
    if "products" not in business_result:
        business_result["products"] = []

    business_result["llm_answer"] = generate_answer(
        user_question,
        business_result
    )

    return business_result


class BusinessRecommendationEngine:

    def __init__(self):
        self.tree       = DecisionTree()
        self.stock      = StockInterceptor()
        self.guardrails = Guardrails()

    def process_business_rules(
        self,
        category,
        collected_information,
        turn_count,
        retrieved_products,
        user_question
    ):
        """
        Parameters
        ----------
        category : str
            Product family detected from the conversation.

        collected_information : dict
            Memory slots collected during the conversation.

        turn_count : int
            Current conversation turn number.

        retrieved_products : list
            Products returned by retrieval.py (RAG).

        user_question : str
            Original customer message.

        Returns
        -------
        dict
            Final business result including llm_answer.
        """

        # ==================================================
        # STEP 1 — Verify category
        # ==================================================

        if not self.tree.category_exists(category):

            business_result = {
                "status":               "UNKNOWN_CATEGORY",
                "allow_recommendation": False,
                "reason":               f"Unknown category '{category}'.",
                "missing_information":  [],
                # Pass RAG results so LLM can show real examples
                # even when category is unknown ("what do you have?")
                "products":             retrieved_products or [],
                "system_prompt":        self.guardrails.build_system_rules(),
            }

            return _send_to_llm(user_question, business_result)

        # ==================================================
        # STEP 2 — Verify minimum conversation length
        # ==================================================

        if turn_count < 3:

            business_result = {
                "status":               "NOT_ENOUGH_TURNS",
                "allow_recommendation": False,
                "reason":               "At least three conversation turns are required before recommending a product.",
                "missing_information":  [],
                # Pass RAG results so LLM can mention real products
                # in early turns (e.g. user asks "what do you have?")
                "products":             retrieved_products or [],
                "system_prompt":        self.guardrails.build_system_rules(),
            }

            return _send_to_llm(user_question, business_result)

        # ==================================================
        # STEP 3 — Verify customer information
        # ==================================================

        tree_result = self.tree.ready(category, collected_information)

        if not tree_result["ready"]:

            business_result = {
                "status":               tree_result["status"],
                "allow_recommendation": False,
                "reason":               tree_result["message"],
                "missing_information":  tree_result["missing"],
                # Pass RAG results so LLM can mention relevant products
                # while asking for the missing info
                "products":             retrieved_products or [],
                "system_prompt":        self.guardrails.build_system_rules(),
            }

            return _send_to_llm(user_question, business_result)

        # ==================================================
        # STEP 4 — Verify RAG results
        # ==================================================

        if len(retrieved_products) == 0:

            business_result = {
                "status":               "NO_PRODUCTS_FOUND",
                "allow_recommendation": False,
                "reason":               "No matching products were found.",
                "missing_information":  [],
                "products":             [],
                "system_prompt":        self.guardrails.build_system_rules(),
            }

            return _send_to_llm(user_question, business_result)

        # ==================================================
        # STEP 5 — Apply stock validation
        # ==================================================

        validated_products = self.stock.replace_if_needed(retrieved_products)

        # ==================================================
        # STEP 6 — Separate product statuses
        # ==================================================

        final_products       = []
        unavailable_products = []
        invalid_products     = []

        for product in validated_products:

            status = product.get("status")

            if status in ["AVAILABLE", "REPLACED"]:
                final_products.append(product)

            elif status == "NO_ALTERNATIVE":
                unavailable_products.append(product)

            elif status == "INVALID_PRODUCT":
                invalid_products.append(product)

        # ==================================================
        # STEP 7 — Nothing recommendable remains
        # ==================================================

        if len(final_products) == 0:

            if len(unavailable_products) > 0:

                business_result = {
                    "status":               "NO_AVAILABLE_PRODUCTS",
                    "allow_recommendation": False,
                    "reason":               "Matching products exist but are unavailable and no replacement exists.",
                    "missing_information":  [],
                    "products":             unavailable_products,
                    "system_prompt":        self.guardrails.build_system_rules(),
                }

            else:

                business_result = {
                    "status":               "BUSINESS_VALIDATION_FAILED",
                    "allow_recommendation": False,
                    "reason":               "No products remain after business validation.",
                    "missing_information":  [],
                    "products":             invalid_products,
                    "system_prompt":        self.guardrails.build_system_rules(),
                }

            return _send_to_llm(user_question, business_result)

        # ==================================================
        # STEP 8 — Business validation succeeded
        # ==================================================

        business_result = {
            "status":               "SUCCESS",
            "allow_recommendation": True,
            "reason":               "Business rules successfully validated.",
            "missing_information":  [],
            "products":             final_products,
            "system_prompt":        self.guardrails.build_system_rules(),
        }

        # ==================================================
        # STEP 9 — Generate final recommendation with Llama
        # ==================================================

        return _send_to_llm(user_question, business_result)