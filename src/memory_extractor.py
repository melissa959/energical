import re

CATEGORY_KEYWORDS = {
    "Sanitaire": [
        "sanitaire", "baignoire", "robinet", "mitigeur", "douche",
        "bidet", "colonne", "infrarouge", "salle de bain", "حمام"
    ],
    "Électricité": [
        "électricité", "electricite", "électrique", "disjoncteur",
        "interrupteur", "prise", "luminaire", "ampoule", "lampe",
        "led", "tableau", "contacteur", "discontacteur", "alarme",
        "minuterie", "كهرباء"
    ],
    "Menuiserie": [
        "menuiserie", "porte", "portillon", "door", "باب"
    ],
    "Pièces de rechange": [
        "pièce", "pieces", "rechange", "sav", "s.a.v", "spare"
    ],
    "Compteurs d'eau": [
        "compteur", "compteur d'eau", "water meter", "عداد"
    ],
    "Électroménager": [
        "électroménager", "electromenager", "appareil", "chauffe-eau",
        "chauffe eau", "chaudière", "chaudiere", "boiler",
        "water heater", "سخان", "chauffage", "gaz", "سخان الماء"
    ],
}

SOUS_CATEGORIE_KEYWORDS = {
    "Chauffage et régulation gaz > Chaudières": [
        "chaudière", "chaudiere", "boiler", "chauffage gaz"
    ],
    "Chauffage et régulation gaz": [
        "chauffage", "régulation gaz", "regulation gaz"
    ],
    "Robinetterie sanitaire": [
        "robinetterie", "robinet sanitaire", "mitigeur", "chromé",
        "cuisine", "bidet", "colonne de douche", "infrarouge", "fly", "razy"
    ],
    "Robinets gaz et accessoires": [
        "robinet gaz", "gaz extérieur", "gaz intérieur"
    ],
    "Robinets multicouches et accessoires": [
        "multicouche", "distributeur multicouche", "accessoire multicouche"
    ],
    "Robinets eau": [
        "robinet eau", "robinets eau"
    ],
    "Baignoires": [
        "baignoire", "bain", "bathtub"
    ],
    "Electricité > Interrupteurs et prises": [
        "interrupteur", "prise", "switch", "apparent", "encastré",
        "etanche", "adenium", "diaa", "noor", "acrylic"
    ],
    "Electricité > Luminaire et éclairage LED": [
        "luminaire", "ampoule", "lampe", "led", "éclairage",
        "eclairage", "culot", "industrielle", "publique"
    ],
    "Electricité > Tableau électrique et protection": [
        "tableau", "disjoncteur", "différentiel", "contacteur",
        "discontacteur", "démarqueur", "minuterie", "protection"
    ],
    "Electricité > Alarme sécurité de la maison": [
        "alarme", "sécurité", "securite", "maison"
    ],
    "Portes": [
        "porte", "portillon", "accessoire porte", "door"
    ],
    "Pièces de rechange pour S.A.V.": [
        "pièce", "rechange", "sav", "chauffe-eau pièce",
        "chaudière pièce", "température constante"
    ],
    "Compteurs d'eau": [
        "compteur", "water meter"
    ],
    "Électroménager": [
        "électroménager", "electromenager"
    ],
    "Hydraulique": [
        "hydraulique", "hydraulic"
    ],
}


REGION_KEYWORDS = {
    "Nord":   ["nord", "alger", "oran", "annaba", "bejaia", "tizi", "blida", "boumerdes"],
    "Sud":    ["sud", "tamanrasset", "adrar", "ouargla", "ghardaia", "biskra", "bechar"],
    "Est":    ["est", "constantine", "setif", "batna", "skikda", "guelma"],
    "Ouest":  ["ouest", "tlemcen", "sidi bel", "mascara", "relizane", "ain temouchent"],
    "Centre": ["centre", "medea", "chlef", "tiaret", "djelfa", "msila"],
}

ENERGIE_KEYWORDS = {
    "gaz":         ["gaz", "gas", "naturel", "قاز"],
    "electrique":  ["électrique", "electrique", "electric", "electricite", "كهربائي"],
    "fioul":       ["fioul", "fuel", "mazout"],
    "bois":        ["bois", "pellet", "granule"],
    "solaire":     ["solaire", "solar", "panneau solaire"],
}

USAGE_KEYWORDS = {
    "chauffage":            ["chauffage", "chauffer", "heating", "تدفئة", "central"],
    "eau chaude sanitaire": ["eau chaude", "sanitaire", "ecs", "douche", "bain"],
    "mixte":                ["mixte", "combiné", "combine", "chauffage et eau"],
}
# ─────────────────────────────────────────────────────────────


class MemoryExtractor:

    @staticmethod
    def extract(message: str) -> dict:

        data = {}
        text = message.lower()

        #  Category 
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                data["category"] = category
                break

       
        for sous_cat, keywords in SOUS_CATEGORIE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                data["sous_categorie"] = sous_cat
                break

       
        budget_match = re.search(
            r"(\d[\d\s]{1,6})\s*(da|dzd|دج)?", text
        )
        if budget_match:
            raw = budget_match.group(1).replace(" ", "")
            try:
                value = int(raw)
                if value >= 100:
                    data["budget"] = value
            except ValueError:
                pass

        
        capacity_match = re.search(
            r"(\d+)\s*(l\b|litres?|litre)", text
        )
        if capacity_match:
            data["capacity"] = int(capacity_match.group(1))

      

      
        surface_match = re.search(
            r"(\d+)\s*(m2|m²|m carré|metres?|مترمربع)", text
        )
        if surface_match:
            data["surface_m2"] = int(surface_match.group(1))

        
        for region, keywords in REGION_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                data["region"] = region
                break

       
        for energie, keywords in ENERGIE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                data["energie"] = energie
                break

        
        for usage, keywords in USAGE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                data["usage"] = usage
                break

      
        if any(kw in text for kw in ["condensation", "condensing", "condensateur"]):
            if any(kw in text for kw in ["sans", "non", "pas", "no"]):
                data["condensation"] = "non"
            else:
                data["condensation"] = "oui"

       

        return data