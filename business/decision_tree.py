# ==========================================================
# decision_tree.py
#
# Phase 4B - Business Recommendation Engine
#
# This module loads Energical's decision trees and checks
# whether enough customer information has been collected
# before allowing a recommendation.
# ==========================================================

import os
import json


class DecisionTree:

    def __init__(self):
        """
        Load the decision tree JSON once when the class
        is created.
        """

        current_dir = os.path.dirname(os.path.abspath(__file__))

        json_path = os.path.join(
            current_dir,
            "..",
            "docs",
            "energical_arbres_decision.json"
        )

        if not os.path.exists(json_path):
            raise FileNotFoundError(
                f"Decision tree file not found:\n{json_path}"
            )

        with open(json_path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    # ------------------------------------------------------
    # Return one product family from the JSON
    # ------------------------------------------------------
    def get_family(self, category):

        arbres = self.data.get("arbres", {})

        return arbres.get(category)

    # ------------------------------------------------------
    # Verify that the requested category exists
    # ------------------------------------------------------
    def category_exists(self, category):

        return self.get_family(category) is not None

    # ------------------------------------------------------
    # Return every field required by the decision tree
    # Example:
    #
    # [
    #   "usage",
    #   "surface_m2",
    #   "energie",
    #   "condensation",
    #   "region"
    # ]
    # ------------------------------------------------------
    def required_fields(self, category):

        tree = self.get_family(category)

        if tree is None:
            return []

        fields = set()

        for rule in tree.get("regles", []):

            for key in rule.get("si", {}):

                fields.add(key)

        return sorted(list(fields))

    # ------------------------------------------------------
    # Find missing customer information
    # ------------------------------------------------------
    def missing_fields(self, category, collected_info):

        required = self.required_fields(category)

        missing = []

        for field in required:

            # Field does not exist
            if field not in collected_info:
                missing.append(field)
                continue

            value = collected_info[field]

            # Empty value
            if value is None:
                missing.append(field)
                continue

            # Empty string
            if isinstance(value, str) and value.strip() == "":
                missing.append(field)

        return missing

    # ------------------------------------------------------
    # Final validation before recommendation
    # ------------------------------------------------------
    def ready(self, category, collected_info):

        # Unknown category
        if not self.category_exists(category):

            return {
                "ready":   False,
                "status":  "UNKNOWN_CATEGORY",
                "missing": [],
                "message": f"The category '{category}' does not exist."
            }

        required = self.required_fields(category)

        # Count filled fields
        filled = [
            field for field in required
            if collected_info.get(field)
        ]

        # Pass if at least 3 fields are filled
        if len(filled) >= 3:

            return {
                "ready":   True,
                "status":  "READY",
                "missing": [],
                "message": "Enough information collected."
            }

        # Not enough filled fields
        missing = [
            field for field in required
            if not collected_info.get(field)
        ]

        return {
            "ready":   False,
            "status":  "MISSING_INFORMATION",
            "missing": missing,
            "message": "Need at least three useful fields."
        }