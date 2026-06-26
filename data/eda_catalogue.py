

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json
import re

DATA_PATH = Path("docs/energical_catalogue_produits.csv")
OUTPUT_PATH = Path("data/chunk_config.json")


def load_catalogue(filepath: Path) -> pd.DataFrame:
    """Charge le catalogue produits."""
    return pd.read_csv(filepath, encoding='utf-8')


def analyze_text_lengths(df: pd.DataFrame) -> Dict:
    """Analyse les longueurs de texte pour déterminer la taille optimale des chunks."""
    
    # Créer un champ texte combiné pour l'analyse
    text_fields = ['nom', 'sous_categorie', 'caracteristiques']
    available_fields = [f for f in text_fields if f in df.columns]
    
    df['combined_text'] = df[available_fields].fillna('').agg(' '.join, axis=1)
    
    # Statistiques de longueur
    char_lengths = df['combined_text'].str.len()
    word_lengths = df['combined_text'].str.split().str.len()
    
    stats = {
        'total_products': len(df),
        'char_length': {
            'mean': float(char_lengths.mean()),
            'std': float(char_lengths.std()),
            'min': int(char_lengths.min()),
            'max': int(char_lengths.max()),
            'q25': float(char_lengths.quantile(0.25)),
            'q50': float(char_lengths.median()),
            'q75': float(char_lengths.quantile(0.75))
        },
        'word_length': {
            'mean': float(word_lengths.mean()),
            'std': float(word_lengths.std()),
            'min': int(word_lengths.min()),
            'max': int(word_lengths.max()),
            'q25': float(word_lengths.quantile(0.25)),
            'q50': float(word_lengths.median()),
            'q75': float(word_lengths.quantile(0.75))
        },
        'recommended_chunk_size': {
            'characters': int(char_lengths.median() + char_lengths.std()),
            'words': int(word_lengths.median() + word_lengths.std()),
            'overlap': 50
        }
    }
    
    # Analyse par catégorie
    if 'sous_categorie' in df.columns:
        category_stats = {}
        for cat in df['sous_categorie'].unique()[:10]:
            cat_df = df[df['sous_categorie'] == cat]
            if len(cat_df) > 0:
                category_stats[cat] = {
                    'count': len(cat_df),
                    'avg_chars': float(cat_df['combined_text'].str.len().mean())
                }
        stats['category_analysis'] = category_stats
    
    # Trouver les produits les plus longs (exemples)
    longest_products = df.nlargest(5, df['combined_text'].str.len())[['nom', 'combined_text']]
    stats['longest_products'] = [
        {'nom': row['nom'], 'length': len(row['combined_text'])}
        for _, row in longest_products.iterrows()
    ]
    
    return stats


def suggest_chunk_strategy(stats: Dict) -> str:
    """Génère une recommandation de stratégie de chunking."""
    
    suggested_chars = stats['recommended_chunk_size']['characters']
    suggested_words = stats['recommended_chunk_size']['words']
    
    return f"""
# STRATÉGIE DE CHUNKING RECOMMANDÉE

## Taille optimale des chunks
- **Caractères**: {suggested_chars} caractères
- **Mots**: {suggested_words} mots
- **Overlap**: {stats['recommended_chunk_size']['overlap']} caractères

## Justification
- Longueur médiane du texte combiné: {stats['char_length']['q50']:.0f} caractères
- Écart-type: {stats['char_length']['std']:.0f} caractères
- La taille suggérée couvre ~75% des produits avec un seul chunk

## Implémentation recommandée
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size={suggested_chars},
    chunk_overlap={stats['recommended_chunk_size']['overlap']},
    separators=["\\n\\n", "\\n", " ", ""],
    length_function=len,
)