

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

DATA_PATH = Path("docs/energical_arbres_decision.json")
OUTPUT_PATH = Path("data/rules_mapping.json")


def load_rules(filepath: Path) -> Dict:
    """Charge le fichier JSON des arbres de décision."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_families_and_questions(rules: Dict) -> Dict:
    """
    Extrait les familles de produits et les questions associées à chaque famille.
    """
    families = {}
    
    # Parcourir les arbres de décision
    for rule in rules:
        family = rule.get('famille', 'inconnue')
        
        if family not in families:
            families[family] = {
                'questions': [],
                'rules_count': 0,
                'attributes': set(),
                'example_flow': []
            }
        
        # Extraire les questions de l'arbre
        if 'questions' in rule:
            for q in rule['questions']:
                question_text = q.get('question', '')
                if question_text:
                    families[family]['questions'].append(question_text)
        
        # Extraire les attributs mentionnés
        if 'attributes' in rule:
            for attr in rule['attributes']:
                families[family]['attributes'].add(attr)
        
        # Compter les règles
        if 'rules' in rule:
            families[family]['rules_count'] += len(rule['rules'])
        
        # Exemple de flow
        if 'flow' in rule and len(families[family]['example_flow']) < 3:
            families[family]['example_flow'].append(rule['flow'])
    
    # Nettoyer les questions (déduplication)
    for family in families:
        families[family]['questions'] = list(dict.fromkeys(families[family]['questions']))
        families[family]['attributes'] = list(families[family]['attributes'])
    
    return families


def generate_question_mapping(families: Dict) -> Dict:
    """
    Génère un mapping des questions par famille et par étape.
    """
    mapping = {}
    
    for family, data in families.items():
        questions = data.get('questions', [])
        
        # Classifier les questions par étape (basé sur les patterns)
        mapping[family] = {
            'step_1': [],  # Questions initiales (identification du besoin)
            'step_2': [],  # Questions de spécification
            'step_3': [],  # Questions de vérification
        }
        
        for q in questions:
            q_lower = q.lower()
            if any(word in q_lower for word in ['besoin', 'quel', 'quelle', 'pourquoi']):
                mapping[family]['step_1'].append(q)
            elif any(word in q_lower for word in ['capacité', 'puissance', 'taille', 'volume']):
                mapping[family]['step_2'].append(q)
            else:
                mapping[family]['step_3'].append(q)
    
    return mapping


def generate_business_rules_template(families: Dict) -> str:
    """
    Génère un template Python pour les règles métier.
    """
    template = '''
# business_rules.py
# Code généré automatiquement à partir de energical_arbres_decision.json

class BusinessRules:
    """Gestionnaire des règles métier par famille de produit."""
    
    FAMILY_RULES = {
'''
    
    for family, data in families.items():
        template += f'        "{family}": {{\n'
        template += f'            "questions": {data["questions"][:5]},\n'
        template += f'            "attributes": {data["attributes"][:5]},\n'
        template += f'            "rules_count": {data["rules_count"]},\n'
        template += '        },\n'
    
    template += '''    }
    
    @staticmethod
    def get_family(family_name: str) -> dict:
        """Retourne les règles pour une famille donnée."""
        return BusinessRules.FAMILY_RULES.get(family_name, {})
    
    @staticmethod
    def get_required_questions(family_name: str) -> list:
        """Retourne les questions à poser pour une famille."""
        return BusinessRules.FAMILY_RULES.get(family_name, {}).get("questions", [])
    
    @staticmethod
    def list_families() -> list:
        """Retourne la liste des familles disponibles."""
        return list(BusinessRules.FAMILY_RULES.keys())
'''
    
    return template


def main():
    """Exécute l'EDA des règles."""
    print("📊 Analyse des arbres de décision...")
    
    # Charger les règles
    rules = load_rules(DATA_PATH)
    print(f"✅ {len(rules)} règles chargées")
    
    # Extraire les familles et questions
    families = extract_families_and_questions(rules)
    
    print(f"\n📂 Familles de produits identifiées:")
    for family, data in families.items():
        print(f"   - {family}: {len(data['questions'])} questions, {data['rules_count']} règles")
    
    # Générer le mapping des questions
    question_mapping = generate_question_mapping(families)
    
    # Sauvegarder le mapping
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'families': families,
            'question_mapping': question_mapping
        }, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Mapping sauvegardé dans: {OUTPUT_PATH}")
    
    # Générer le template Python
    template = generate_business_rules_template(families)
    template_path = Path("src/business_rules.py")
    template_path.parent.mkdir(parents=True, exist_ok=True)
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template)
    print(f"✅ Template business_rules.py sauvegardé dans: {template_path}")
    
    # Afficher les questions par famille
    print(f"\n📋 Questions par famille:")
    for family, data in families.items():
        questions = data.get('questions', [])
        if questions:
            print(f"\n   {family}:")
            for q in questions[:3]:
                print(f"      - {q}")
            if len(questions) > 3:
                print(f"      ... et {len(questions) - 3} autres")


if __name__ == "__main__":
    main()