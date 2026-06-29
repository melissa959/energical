

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


    def get_family(self, category):

        arbres = self.data.get("arbres", {})

        return arbres.get(category)

  
    def category_exists(self, category):

        return self.get_family(category) is not None

  
    def required_fields(self, category):

        tree = self.get_family(category)

        if tree is None:
            return []

        fields = set()

        for rule in tree.get("regles", []):

            for key in rule.get("si", {}):

                fields.add(key)

        return sorted(list(fields))

 
    def missing_fields(self, category, collected_info):

        required = self.required_fields(category)

        missing = []

        for field in required:

            
            if field not in collected_info:
                missing.append(field)
                continue

            value = collected_info[field]

          
            if value is None:
                missing.append(field)
                continue

            
            if isinstance(value, str) and value.strip() == "":
                missing.append(field)

        return missing

  
    def ready(self, category, collected_info):

      
        if not self.category_exists(category):

            return {
                "ready":   False,
                "status":  "UNKNOWN_CATEGORY",
                "missing": [],
                "message": f"The category '{category}' does not exist."
            }

        required = self.required_fields(category)

      
        filled = [
            field for field in required
            if collected_info.get(field)
        ]

      
        if len(filled) >= 3:

            return {
                "ready":   True,
                "status":  "READY",
                "missing": [],
                "message": "Enough information collected."
            }

      
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