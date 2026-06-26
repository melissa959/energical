import json
import re
import os

class ScalableIntentMatcher:
    def __init__(self, catalog_path="patterns_catalog.json"):
        self.catalog_path = catalog_path
        self.patterns = {
            "darija_arabic": [],
            "darija_latin": [],
            "french": []
        }
        self.load_catalog()

    def load_catalog(self):
        """Charge les mots depuis le JSON et compile les expressions régulières."""
        # Si le fichier n'existe pas, on le crée avec des listes vides
        if not os.path.exists(self.catalog_path):
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self.patterns = json.load(f)
        
        # Compilation dynamique des Regex avec protection contre les listes vides
        self.rx_ar = re.compile(r'\b(' + '|'.join(map(re.escape, self.patterns["darija_arabic"])) + r')\b', re.IGNORECASE) if self.patterns["darija_arabic"] else None
        self.rx_lat = re.compile(r'\b(' + '|'.join(map(re.escape, self.patterns["darija_latin"])) + r')\b', re.IGNORECASE) if self.patterns["darija_latin"] else None
        self.rx_fr = re.compile(r'\b(' + '|'.join(map(re.escape, self.patterns["french"])) + r')\b', re.IGNORECASE) if self.patterns["french"] else None

    def enrich_catalog(self, category: str, new_word: str) -> bool:
        """
        Permet d'ajouter dynamiquement un nouveau mot découvert 
        dans le dictionnaire permanent (JSON).
        """
        if category not in self.patterns:
            return False
        
        clean_word = new_word.strip().lower()
        
        # Éviter les doublons
        if clean_word and clean_word not in self.patterns[category]:
            self.patterns[category].append(clean_word)
            
            # Sauvegarde physique immédiate sur le disque
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
                
            # Re-compiler les regex pour appliquer le changement en temps réel
            self.load_catalog()
            return True
        return False

    def extract_keywords(self, text: str) -> str:
        """Analyse le texte et extrait les mots clés connus."""
        if not text:
            return ""
            
        tokens = []
        if self.rx_ar: tokens.extend(self.rx_ar.findall(text))
        if self.rx_lat: tokens.extend(self.rx_lat.findall(text))
        if self.rx_fr: tokens.extend(self.rx_fr.findall(text))
        
        return " ".join(list(set([t for t in tokens if t])))

# --- Exemple de cycle de vie pendant le Hackathon ---
if __name__ == "__main__":
    matcher = ScalableIntentMatcher()
    
    # 1. Test classique d'extraction
    query = "khasser chofaj svpl"
    print(f"Mots extraits : {matcher.extract_keywords(query)}")
    
    # 2. Scénario d'apprentissage automatique (Scalabilité)
    # Imaginons que l'utilisateur écrit un nouveau mot comme "takhssir" ou "bomba"
    print("\n[Système] Détection d'un nouveau mot technique Darija par le système...")
    
    # On enrichit la base de données de manière persistante
    added = matcher.enrich_catalog("darija_latin", "bomba")
    if added:
        print("[Succès] Le dictionnaire JSON a été mis à jour sans couper le serveur !")
        
    # 3. Vérification immédiate : le mot est maintenant reconnu !
    new_query = "bghit bomba dial gaz"
    print(f"Nouvelle extraction : {matcher.extract_keywords(new_query)}")