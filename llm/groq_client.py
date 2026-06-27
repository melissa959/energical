"""
groq_client.py
Energical AI Sales Assistant
Français / Darija DZ / English
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ------------------------------------------------------------------
# Session state — stocké dans un dict passé depuis Streamlit session_state
# NE PAS utiliser de variables globales (Streamlit rerun les reset)
# ------------------------------------------------------------------
_session = {"greeted": False, "turn_count": 0, "current_category": ""}


def reset_session():
    _session["greeted"] = False
    _session["turn_count"] = 0
    _session["current_category"] = ""


# ------------------------------------------------------------------
# Static catalog
# ------------------------------------------------------------------
CATALOG_OVERVIEW = """\
Energical propose 4 familles de produits :

1. CHAUFFAGE & CHAUFFE-EAU
   - Chaudieres murales gaz (condensation ou standard)
   - Chauffe-eau instantanes et a accumulation
   - Pour : chauffage central et eau chaude sanitaire

2. CLIMATISATION
   - Climatiseurs split residentiels et semi-pro
   - Pompes a chaleur reversibles (chaud + froid)
   - Pour : appartements, maisons, bureaux

3. ROBINETTERIE & SANITAIRE
   - Mitigeurs thermostatiques et mecaniques
   - Robinets cuisine, salle de bain, lavabo
   - Filtres a gaz et accessoires plomberie

4. VISIOPHONIE & CONTROLE D'ACCES
   - Visiphones connectes 2 a 4 familles
   - Interphones avec badge RFID
   - Systemes sonnette video pour immeubles collectifs"""

# ------------------------------------------------------------------
# Darija + English glossary
# ------------------------------------------------------------------
LANGUAGE_GLOSSARY = """\
DARIJA ALGERIEN :
bghit/nheb=je veux | wach/wesh=est-ce que | choufage/chaufage/dafa=chauffage
skhana/sekhan=chauffe-eau | dar=maison | kbir/kbira=grand | sghir/sghira=petit
blasti/3andi=chez moi | qaddach/bchhal=combien | clim/baroud/moukayif=climatiseur
flouss=argent | ghali=cher | rkhis=pas cher | mzyan/zwina=bien | kollchi/koulchi=tout

ENGLISH :
boiler=chaudiere | water heater=chauffe-eau | heating=chauffage | AC/air con=climatiseur
tap/faucet=robinet | intercom/doorbell=visiophone | how much=prix | show me=catalogue"""

# ------------------------------------------------------------------
# Categories logiques et leurs mots-cles
# ------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "chaudiere": [
        "chaudiere", "chauffage", "chauffe", "chauffer", "chaufage", "dafa",
        "condensation", "boiler", "heating", "chauffe-eau", "chauffe eau",
        "eau chaude", "skhana", "sekhan", "choufage"
    ],
    "climatisation": [
        "climatisation", "climatiseur", "clim", "baroud", "moukayif",
        "froid", "reversible", "split", "ac", "air con",
        "pompe a chaleur", "pompe chaleur"
    ],
    "robinetterie": [
        "robinet", "mitigeur", "douche", "bain", "lavabo",
        "cuisine", "salle de bain", "plomberie", "tap", "faucet",
        "amen", "thermostatique", "mecanique"
    ],
    "visiophone": [
        "visiophone", "interphone", "sonnette", "video", "rfid", "badge",
        "famille", "familles", "immeuble", "acces", "intercom", "doorbell",
        "portier", "videophone"
    ],
}

# Mots qui NE sont PAS des categories produits (pour eviter faux positifs)
# ex: "gaz" seul peut etre filtre gaz robinetterie, pas forcement chaudiere
PRODUCT_NOISE_WORDS = ["gaz", "standard", "sanitaire"]

# Mots-cles produits hors-categorie a EXCLURE des resultats chauffage
IRRELEVANT_PRODUCT_KEYWORDS = [
    "friteuse", "four", "micro-onde", "aspirateur", "cafetiere",
    "electromenager", "cuisine", "cuisson", "congelateur", "refrigerateur"
]


def detect_logical_category(user_question: str, products: list) -> str:
    """Detecte la categorie depuis les mots du client en priorite."""
    text = user_question.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return ""


def filter_relevant_products(products: list, category: str) -> list:
    """
    Filtre les produits hors-sujet.
    Ex: enleve friteuses quand le client parle de chauffage.
    """
    if not category or not products:
        return products

    filtered = []
    for p in products:
        nom = p.get("metadata", {}).get("nom", "").lower()
        desc = p.get("document_text", "").lower()
        full_text = nom + " " + desc

        # Exclure produits clairement hors-categorie
        if any(noise in full_text for noise in IRRELEVANT_PRODUCT_KEYWORDS):
            continue

        # Pour chaudiere : garder seulement produits chauffage
        if category == "chaudiere":
            chaudiere_words = ["chaudiere", "chauffe-eau", "chauffe eau", "filtre", "condensation",
                               "thermocontact", "sonde", "echangeur", "bruleur", "vanne", "circulateur",
                               "expansion", "pressostat", "pilote", "panneau", "commande"]
            if any(w in full_text for w in chaudiere_words):
                filtered.append(p)
        else:
            filtered.append(p)

    return filtered if filtered else products  # fallback si tout filtre


# ------------------------------------------------------------------
# Intent detection
# ------------------------------------------------------------------
DISCOVERY_PHRASES = [
    "qu'est-ce que vous avez", "qu'est ce que vous avez", "ce que vous avez",
    "quels produits", "vos produits", "votre catalogue", "what do you have",
    "what products", "show me", "liste", "tous les produits", "tous vos produits",
    "catalogue", "gamme", "proposez vous", "proposez-vous",
    "avez vous", "avez-vous", "propose moi", "proposez moi",
    "kollchi", "koulchi", "donne moi ce que vous avez",
    "qu'est ce que vous proposez", "que proposez vous",
    "qu'est-ce que vous proposez", "que vous avez",
    "quels sont vos produits", "que vous proposer",
    "vous proposez quoi", "que vous proposez", "que proposez-vous",
]

BEST_PHRASES = [
    "meilleur", "mieux", "recommande", "lequel choisir", "quel est le mieux",
    "quel est le meilleur", "best", "which one", "compare",
    "difference", "differnce", "choisir entre", "comment choisir",
    "aide moi", "aidez moi", "conseille", "conseillez", "help",
    "de quoi tu me conseille", "tu me conseille", "conseil",
    "resume", "resumee", "en resume", "en bref", "synthese",
]

SWITCH_CATEGORY_PHRASES = [
    "a part", "pas ca", "pas cela",
    "autre categorie", "pas chauffage", "pas climatisation",
    "pas robinetterie", "pas visiophone",
    "autre que", "changer", "change",
]

VAGUE_PHRASES = [
    "bonjour", "salut", "salam", "coucou", "hello", "hi", "hey",
    "bonsoir", "bjr", "slt", "cc", "salutations",
    "je cherche des informations", "je veux des informations",
    "je cherche quelque chose", "j'ai besoin d'aide",
    "je veux savoir", "dites moi", "je suis interesse",
]


def _intent(text: str, phrases: list) -> bool:
    t = text.lower().strip().rstrip("?!.")
    return any(p in t for p in phrases)


def is_discovery_intent(text: str) -> bool:
    return _intent(text, DISCOVERY_PHRASES)

def is_best_intent(text: str) -> bool:
    return _intent(text, BEST_PHRASES)

def is_switch_intent(text: str) -> bool:
    return _intent(text, SWITCH_CATEGORY_PHRASES)

def is_vague_message(text: str) -> bool:
    t = text.lower().strip().rstrip("?!.")
    if is_discovery_intent(text) or is_switch_intent(text):
        return False
    if len(t.split()) <= 2:
        return True
    for phrase in VAGUE_PHRASES:
        if phrase in t:
            all_keywords = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]
            if not any(kw in t for kw in all_keywords):
                return True
    return False


# ------------------------------------------------------------------
# Product context builder
# ------------------------------------------------------------------
def _product_context(products: list) -> str:
    if not products:
        return "AUCUN PRODUIT DISPONIBLE."
    blocks = []
    for i, p in enumerate(products, 1):
        m    = p.get("metadata", {})
        nom  = m.get("nom", "Produit")
        prix = m.get("prix", "N/A")
        sto  = m.get("statut_stock", "")
        desc = p.get("document_text", "")
        pid  = p.get("id", "")
        repl = " [REMPLACEMENT - modele original en rupture]" if p.get("status") == "REPLACED" else ""

        prix_display  = f"{prix} DA" if prix and prix not in ("N/A", "0") else "Prix non disponible"
        stock_display = "En stock" if sto == "En stock" else (f"Stock: {sto}" if sto else "Non precise")

        blocks.append(
            f"PRODUIT {i}:\n"
            f"  Nom           : {nom}{repl}\n"
            f"  Reference     : {pid}\n"
            f"  Prix          : {prix_display}\n"
            f"  Disponibilite : {stock_display}\n"
            f"  Description   : {desc}"
        )
    return "\n\n".join(blocks)


# ------------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------------
def generate_answer(user_question: str, business_result: dict) -> str:

    status   = business_result.get("status", "SUCCESS")
    products = business_result.get("products", [])

    is_first = not _session["greeted"]
    _session["greeted"] = True
    _session["turn_count"] += 1

    # Detecter la categorie depuis les mots du client
    category = detect_logical_category(user_question, products)

    # Persister la categorie en session si on en trouve une
    if category:
        _session["current_category"] = category
    elif _session["current_category"]:
        # Recuperer la categorie de la conversation si le message actuel est vague
        category = _session["current_category"]

    # Filtrer les produits hors-sujet (ex: friteuses dans chauffage)
    products = filter_relevant_products(products, category)

    prod_ctx     = _product_context(products)
    has_products = len(products) > 0
    nb_products  = len(products)

    # Intents
    discovery = is_discovery_intent(user_question)
    best      = is_best_intent(user_question)
    vague     = is_vague_message(user_question)
    switch    = is_switch_intent(user_question)

    greeting = "Bonjour et bienvenue chez Energical !\n\n" if is_first else ""

    # ----------------------------------------------------------------
    # CAS 1 : Message vague sans categorie => accueil
    # ----------------------------------------------------------------
    if vague and not category:
        task = f"""\
{greeting}Le client dit quelque chose de vague (bonjour, je cherche...).

REPONSE :
{"Accueille chaleureusement le client." if is_first else "Reponds poliment."}
Dis en une phrase que Energical est specialiste en 4 domaines.
Demande : "Quel type de produit recherchez-vous ?"

INTERDIT : Aucun produit specifique. Aucune supposition de categorie."""

    # ----------------------------------------------------------------
    # CAS 2 : Catalogue global
    # ----------------------------------------------------------------
    elif discovery and not category:
        task = f"""\
{greeting}Le client veut voir tout le catalogue.

REPONSE :
Presente les 4 familles clairement et de facon engageante.
Termine par : "Laquelle de ces categories vous interesse ?"

{CATALOG_OVERVIEW}

INTERDIT : Aucun produit specifique."""

    # ----------------------------------------------------------------
    # CAS 3 : Changement de categorie
    # ----------------------------------------------------------------
    elif switch:
        _session["current_category"] = ""  # Reset categorie
        task = f"""\
Le client veut changer de sujet.

REPONSE :
1. Acquiesce brievement.
2. Presente les 4 familles.
3. Demande laquelle l'interesse.

{CATALOG_OVERVIEW}

INTERDIT : Ne mentionne plus l'ancienne categorie."""

    # ----------------------------------------------------------------
    # CAS 4 : Demande de conseil / comparaison / resume
    # ----------------------------------------------------------------
    elif best and has_products:
        task = f"""\
Le client demande un conseil, une comparaison ou un resume sur {category or "les produits"}.

REPONSE :
1. Va DROIT AU BUT. Resume les options disponibles en 2-3 phrases max.
2. Compare clairement : differences de prix, puissance, usage.
3. Donne UNE recommandation concrete selon le besoin type.
4. Pose UNE seule question si besoin de preciser.

PRODUITS :
{prod_ctx}

REGLES :
- Sois concis et direct, pas de blabla
- "resume" = reponse courte et claire, pas plus longue que avant
- Ne redis pas tout ce que tu as deja dit"""

    # ----------------------------------------------------------------
    # CAS 5 : Categorie identifiee + produits disponibles
    # ----------------------------------------------------------------
    elif category and has_products:

        comparison_section = ""
        if nb_products > 1:
            comparison_section = f"""
COMPARAISON OBLIGATOIRE (apres la liste) :
- Explique les differences reelles entre les {nb_products} produits
- Differences de : puissance/capacite, prix, usage recommande, technique
- Dis clairement : "Le produit X est ideal si... Le produit Y convient mieux si..."
- NE DIS PAS juste "ils different par leurs references" — sois precis"""

        followup = {
            "chaudiere":     "Pour mieux vous orienter : c'est pour un appartement ou une maison, et combien de m2 ?",
            "climatisation": "C'est pour quelle superficie et quelle region d'Algerie ?",
            "robinetterie":  "C'est pour la cuisine, la salle de bain ou la douche ?",
            "visiophone":    "C'est pour combien de familles et avec ou sans badge RFID ?",
        }.get(category, "Pouvez-vous preciser votre besoin ?")

        task = f"""\
{greeting}Le client s'interesse au : {category.upper()}
Produits trouves : {nb_products}

REPONSE :
1. Une phrase de confirmation (pas de "bonjour" si pas premier message).
2. Liste chaque produit : nom, reference, prix, stock, description utile.
3. {comparison_section if nb_products > 1 else "Decris bien ce produit et son utilite."}
4. Question finale : "{followup}"

PRODUITS :
{prod_ctx}

REGLES :
- Numerote chaque produit
- Separe avec "---"
- Langage naturel et commercial
- Ne redis JAMAIS "bonjour" ou "je suis Karim" si pas premier message
- UNE seule question a la fin"""

    # ----------------------------------------------------------------
    # CAS 6 : Categorie identifiee, pas de produits
    # ----------------------------------------------------------------
    elif category and not has_products:
        question = {
            "chaudiere":     "Pour vous proposer la chaudiere ideale : c'est pour chauffer combien de m2 ?",
            "climatisation": "Pour la clim ideale : superficie de la piece et region ?",
            "robinetterie":  "C'est pour quel usage — cuisine, salle de bain ou douche ?",
            "visiophone":    "C'est pour combien de familles ?",
        }.get(category, f"Pouvez-vous preciser votre besoin en {category} ?")

        task = f"""\
{greeting}Le client s'interesse au {category.upper()} mais pas de produits trouves encore.

REPONSE :
1. Confirme que Energical propose des produits en {category}.
2. Pose cette question : "{question}"

INTERDIT : Aucun produit specifique. Aucune supposition."""

    # ----------------------------------------------------------------
    # CAS 7 : Recommandation finale (SUCCESS)
    # ----------------------------------------------------------------
    elif status == "SUCCESS" and has_products:
        task = f"""\
Recommandation finale pour le client.

REPONSE :
1. Recommande le produit le plus adapte.
2. Explique pourquoi en 2-3 raisons concretes.
3. Prix et reference clairement.
4. "Souhaitez-vous commander ce modele ou avez-vous d'autres questions ?"

PRODUITS :
{prod_ctx}"""

    # ----------------------------------------------------------------
    # CAS 8 : Aucun produit trouve
    # ----------------------------------------------------------------
    elif status in ("NO_PRODUCTS_FOUND", "UNKNOWN_CATEGORY"):
        task = f"""\
{greeting}Aucun produit trouve.

REPONSE :
1. Informe poliment.
2. Rappelle les 4 familles disponibles.
3. Demande ce qui interesse le client.

{CATALOG_OVERVIEW}"""

    # ----------------------------------------------------------------
    # CAS 9 : Rupture de stock
    # ----------------------------------------------------------------
    elif status == "NO_AVAILABLE_PRODUCTS":
        task = f"""\
Rupture de stock.

REPONSE :
1. Informe avec tact.
2. Propose d'etre recontacte.
3. Propose alternatives si possible.

PRODUITS EN RUPTURE :
{prod_ctx}"""

    # ----------------------------------------------------------------
    # CAS 10 : Fallback
    # ----------------------------------------------------------------
    else:
        task = f"""\
{greeting}Reponds naturellement. Contexte Energical.
{"Produits disponibles :\n" + prod_ctx if has_products else "Propose les 4 familles si pertinent.\n" + CATALOG_OVERVIEW}"""

    # ----------------------------------------------------------------
    # SYSTEM PROMPT
    # ----------------------------------------------------------------
    system_prompt = f"""\
Tu es Karim, conseiller commercial senior chez Energical Algerie.

TON ROLE :
- Comprendre exactement ce que veut le client
- Presenter UNIQUEMENT les produits pertinents pour sa demande
- Expliquer les differences entre produits de facon precise et utile
- Aider le client a faire le meilleur choix

REGLES ABSOLUES :
1. Reponds dans la langue du client (francais, darija, anglais)
2. Ne dis JAMAIS "Bonjour" ou "je suis Karim" sauf au tout premier message
3. Ne pose JAMAIS plus d'UNE question a la fois
4. Ne montre JAMAIS de produits hors-categorie (ex: friteuse si client demande chauffage)
5. Quand plusieurs produits : explique les vraies differences, ne sois pas vague
6. "resume" ou "en bref" = reponse COURTE et directe
7. Sois naturel et commercial, pas robotique ni repetitif

GLOSSAIRE :
{LANGUAGE_GLOSSARY}"""

    user_prompt = f"""\
Message du client : {user_question}

{task}

Reponds maintenant de facon claire et utile."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=900,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
    )

    return response.choices[0].message.content