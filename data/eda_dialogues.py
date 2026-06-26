

import json
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple

# Configuration
DATA_PATH = Path("docs/energical_dialogues_clients.json")
OUTPUT_PATH = Path("prompts/few_shot_examples.txt")


def load_dialogues(filepath: Path) -> List[Dict]:
    """Charge le fichier JSON des dialogues clients."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_keywords(dialogues: List[Dict]) -> Tuple[Counter, Counter, Dict]:
    """
    Extrait les mots-clés des dialogues.
    Retourne : (mots_darija, mots_francais, exemples_par_famille)
    """
    darija_words = Counter()
    french_words = Counter()
    family_examples = {}
    
    # Listes de mots Darija courants (à enrichir)
    darija_patterns = [
        r'\b(شنو|واش|كيفاش|مليح|حاب|نحوس|قدر|شكون|علاش|فاش|دوك|هذا|هذي|هاذو|راني|نحنا|كوم|نتا|نتي|الزوالي)\b',
        r'\b(باش|بالزاف|شوية|بزاف|قاع|كلش|حتى|والو|باهي|صحيح|مزيان|زين)\b',
    ]
    
    for dialogue in dialogues:
        family = dialogue.get('famille', 'inconnue')
        if family not in family_examples:
            family_examples[family] = []
        
        for turn in dialogue.get('dialogues', []):
            # Nettoyer le texte
            text = turn.get('client', '') + ' ' + turn.get('agent', '')
            text = text.lower()
            
            # Extraire les mots Darija
            for pattern in darija_patterns:
                matches = re.findall(pattern, text, re.UNICODE)
                darija_words.update(matches)
            
            # Extraire les mots Français techniques
            french_pattern = r'\b(chaudière|chauffe-eau|radiateur|robinet|vanne|disjoncteur|interrupteur|luminaire|câble|prise|thermostat|pompe|cuve|chauffage|eau|gaz|électricité)\b'
            matches = re.findall(french_pattern, text, re.UNICODE)
            french_words.update(matches)
            
            # Collecter des exemples pour chaque famille
            if len(family_examples[family]) < 3:
                family_examples[family].append({
                    'client': turn.get('client', ''),
                    'response': turn.get('agent', ''),
                    'produit': turn.get('produit_recommande', 'inconnu')
                })
    
    return darija_words, french_words, family_examples


def generate_few_shot_prompt(family_examples: Dict) -> str:
    """Génère le prompt few-shot à partir des exemples."""
    prompt_parts = [
        "# EXEMPLES DE DIALOGUES CLIENTS",
        "# Ces exemples montrent comment les clients parlent en Darija/Français",
        ""
    ]
    
    for family, examples in family_examples.items():
        prompt_parts.append(f"## Famille: {family.upper()}")
        for i, ex in enumerate(examples[:2], 1):
            prompt_parts.append(f"### Exemple {i}:")
            prompt_parts.append(f"Client: {ex['client']}")
            prompt_parts.append(f"Agent: {ex['response']}")
            if ex['produit'] != 'inconnu':
                prompt_parts.append(f"Produit recommandé: {ex['produit']}")
            prompt_parts.append("")
    
    # Ajouter les instructions générales
    prompt_parts.extend([
        "",
        "# DIRECTIVES POUR L'AGENT",
        "- Réponds toujours en Darija (ou en Français si le client a commencé en Français)",
        "- Sois naturel et amical, comme un vrai vendeur algérien",
        "- Pose des questions pour cerner le besoin avant de recommander",
        "- Recommande un produit précis du catalogue avec son prix et ses caractéristiques",
        "- Si le produit est en rupture, propose une alternative",
        ""
    ])
    
    return '\n'.join(prompt_parts)


def main():
    """Exécute l'EDA des dialogues."""
    print("📊 Analyse des dialogues clients...")
    
    # Charger les dialogues
    dialogues = load_dialogues(DATA_PATH)
    print(f"✅ {len(dialogues)} dialogues chargés")
    
    # Extraire les mots-clés
    darija, french, examples = extract_keywords(dialogues)
    
    print(f"\n📝 Mots Darija les plus fréquents:")
    for word, count in darija.most_common(15):
        print(f"   {word}: {count}")
    
    print(f"\n🇫🇷 Mots Français techniques les plus fréquents:")
    for word, count in french.most_common(10):
        print(f"   {word}: {count}")
    
    # Générer le prompt few-shot
    few_shot_prompt = generate_few_shot_prompt(examples)
    
    # Sauvegarder
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(few_shot_prompt)
    print(f"\n✅ Prompt few-shot sauvegardé dans: {OUTPUT_PATH}")
    
    # Afficher les familles disponibles
    print(f"\n📂 Familles de produits identifiées:")
    for family in examples.keys():
        print(f"   - {family}")


if __name__ == "__main__":
    main()