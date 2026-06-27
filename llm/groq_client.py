"""
llm/groq_client.py
==================
Energical AI Sales Assistant v7

FIXES :
- FIX C : message de politesse -> accusé de réception simple, pas de relance
- FIX B : last_recommended passé au prompt pour zoom précis
- _pick_followup_question : alias energie/combustible
- Zoom 1 produit : prompt strict "ce produit uniquement"
- Pas d'emojis
"""

import os
import re
import time
from collections import deque
from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()

_session = {
    "greeted": False,
    "current_category": "",
    "turn_count": 0,
}

def reset_session():
    _session["greeted"] = False
    _session["current_category"] = ""
    _session["turn_count"] = 0


class _Throttler:
    def __init__(self, rpm=15):
        self.rpm = rpm
        self._times = deque()

    def wait_if_needed(self):
        now = time.time()
        while self._times and now - self._times[0] > 60:
            self._times.popleft()
        if len(self._times) >= self.rpm:
            sleep = 61 - (now - self._times[0])
            if sleep > 0:
                time.sleep(sleep)
        self._times.append(time.time())

_throttler = _Throttler()

_CATALOG = """\
- Chauffage et chauffe-eau : chaudieres murales gaz, chauffe-eau instantanes et a accumulation
- Climatisation : climatiseurs splits, pompes a chaleur reversibles
- Robinetterie et sanitaire : mitigeurs, robinets, filtres a gaz, accessoires plomberie
- Visiophonie et controle d'acces : visiphones, interphones RFID, portiers video"""

_GLOSSARY = """\
Darija : bghit/nheb = je veux | choufage/chaufage/dafa = chauffage
skhana = chauffe-eau | dar = maison | qaddach/bchhal = combien
clim/baroud = climatiseur | zwina/mzyan = bien
ghali = cher | rkhis = pas cher"""

_CAT_KEYWORDS = {
    "chaudiere":     ["chaudiere", "chauffage", "chaufage", "choufage",
                      "chauffe-eau", "chauffe eau", "eau chaude", "boiler", "skhana",
                      "sekhan", "dafa", "condensation", "heating"],
    "climatisation": ["clim", "climatiseur", "climatisation", "baroud", "moukayif",
                      "froid", "split", "pompe a chaleur", "pompe chaleur", "ac"],
    "robinetterie":  ["robinet", "mitigeur", "douche", "lavabo", "plomberie",
                      "thermostatique", "robinetterie", "amen"],
    "visiophone":    ["visiophone", "interphone", "sonnette", "rfid", "badge",
                      "immeuble", "acces", "intercom", "portier"],
}

def detect_category(text: str) -> str:
    t = text.lower()
    for cat, words in _CAT_KEYWORDS.items():
        if any(w in t for w in words):
            return cat
    return ""

def is_vague_message(text: str) -> bool:
    t = text.lower().strip()
    greetings = ["bonjour", "salut", "salam", "hello", "hi", "bonsoir", "bjr", "slt", "hey"]
    if any(g in t for g in greetings):
        all_kw = [w for ws in _CAT_KEYWORDS.values() for w in ws]
        if not any(k in t for k in all_kw):
            return True
    if len(t.split()) <= 2 and not detect_category(t):
        return True
    return False

def is_discovery_intent(text: str) -> bool:
    phrases = ["qu'est-ce que vous avez", "quels produits", "votre catalogue",
               "catalogue", "tous vos produits", "que proposez", "gamme",
               "kollchi", "koulchi", "tout ce que vous avez"]
    t = text.lower()
    return any(p in t for p in phrases)


def _build_product_context(products: list) -> str:
    if not products:
        return ""
    lines = []
    for i, p in enumerate(products, 1):
        m        = p.get("metadata", {})
        nom      = m.get("nom", "Produit")
        prix     = m.get("prix", "")
        sto      = m.get("statut_stock", "")
        desc     = p.get("document_text", "")
        pid      = p.get("id", "")
        replaced = p.get("status") == "REPLACED"

        prix_str = f"{prix} DA" if prix and str(prix) not in ("0", "N/A", "") else "Prix non communique"
        sto_str  = "En rupture de stock" if "rupture" in str(sto).lower() else "En stock"
        note     = " [Modele de remplacement - original en rupture]" if replaced else ""

        lines.append(
            f"Produit {i} :\n"
            f"  Nom          : {nom}{note}\n"
            f"  Reference    : {pid}\n"
            f"  Prix         : {prix_str}\n"
            f"  Disponibilite: {sto_str}\n"
            f"  Description  : {desc}"
        )
    return "\n\n".join(lines)


def _format_memory(mem: dict) -> str:
    if not mem:
        return "Rien de connu pour l'instant."
    labels = {
        "surface_m2":        "Superficie a chauffer",
        "energie":           "Type d'energie",
        "condensation":      "Chaudiere a condensation",
        "region":            "Region",
        "usage":             "Usage",
        "combustible":       "Combustible",
        "debit":             "Debit souhaite",
        "type_chauffe":      "Type de chauffe",
        "puissance_kw":      "Puissance souhaitee",
        "superficie":        "Superficie a climatiser",
        "type_installation": "Type d'installation",
        "boutons_4f":        "Nombre de familles",
        "interphone":        "Type d'interphone",
        "rfid_2f":           "Acces RFID",
    }
    lines = []
    for k, v in mem.items():
        if v is not None and str(v).strip() not in ("", "None"):
            lines.append(f"  - {labels.get(k, k)} : {v}")
    return "\n".join(lines) if lines else "Rien de connu pour l'instant."


_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]

_FIELDS_ORDER = {
    "chaudiere": [
        ("surface_m2",   "C'est pour chauffer combien de metres carres ?"),
        ("energie",      "Vous etes au gaz naturel ou au butane ?"),
        ("condensation", "Vous preferez une chaudiere a condensation, plus economique en consommation ?"),
        ("usage",        "C'est pour un appartement ou une maison individuelle ?"),
    ],
    "climatisation": [
        ("superficie",        "Quelle superficie souhaitez-vous climatiser ?"),
        ("region",            "Dans quelle region d'Algerie etes-vous ?"),
        ("type_installation", "C'est une nouvelle installation ou un remplacement ?"),
    ],
    "robinetterie": [
        ("usage", "C'est pour la cuisine, la salle de bain ou la douche ?"),
    ],
    "visiophone": [
        ("boutons_4f", "C'est pour combien de familles ou d'appartements ?"),
        ("interphone", "Vous voulez juste l'audio ou aussi la video ?"),
        ("rfid_2f",    "Vous souhaitez un acces par badge RFID ?"),
    ],
}

_FIELD_ALIASES = {
    "energie": ["energie", "combustible"],
}

def _pick_followup_question(mem: dict, category: str) -> str:
    known = {k for k, v in mem.items() if v is not None and str(v).strip() not in ("", "None")}
    energie_val = str(mem.get("energie", "") or mem.get("combustible", "")).lower()
    if any(kw in energie_val for kw in ["electrique", "electricite", "gaz", "butane"]):
        known.add("energie")
        known.add("combustible")
    for field, question in _FIELDS_ORDER.get(category, []):
        aliases = _FIELD_ALIASES.get(field, [field])
        if not any(a in known for a in aliases):
            return question
    return ""


def generate_answer(user_question: str, business_result: dict) -> str:

    is_first     = not _session["greeted"]
    _session["greeted"] = True
    _session["turn_count"] += 1

    cat_from_msg = detect_category(user_question)
    if cat_from_msg:
        _session["current_category"] = cat_from_msg
    category = _session["current_category"]

    products          = business_result.get("products", [])
    mem               = business_result.get("collected_information", {})
    is_followup       = business_result.get("is_followup", False)
    is_courtesy       = business_result.get("is_courtesy", False)
    last_recommended  = business_result.get("last_recommended")
    has_products      = len(products) > 0
    prod_ctx          = _build_product_context(products)
    mem_str           = _format_memory(mem)
    followup_q        = _pick_followup_question(mem, category)

    _short_re = [
        r'^\d+(\s*(m2|m²|metres?))?$',
        r'^(gaz(\s+naturel)?|butane|electricite|electrique)$',
        r'^(oui|non|yes|no|iyeh|la)$',
        r'^(appartement|maison|villa)$',
        r'^condensation$',
        r'^\d+\s*(kw)?$',
    ]
    is_short_memory_answer = is_followup and any(
        re.match(p, user_question.lower().strip()) for p in _short_re
    )

    # ---- FIX C : message de politesse ------------------------------------

    if is_courtesy:
        user_prompt = f"""\
Le client a dit : "{user_question}"
C'est un message de politesse ou de fin d'echange.
Reponds de facon breve et chaleureuse (1-2 phrases maximum).
Si le client semble avoir termine, propose-lui de revenir si besoin.
Ne relance pas de recommandation non demandee. Pas d'emojis."""

    # ---- Premier message -------------------------------------------------

    elif is_first:
        if is_vague_message(user_question) and not category:
            user_prompt = f"""\
Le client envoie son premier message : "{user_question}"

Redige un message d'accueil en francais avec :
1. "Bonjour, nous sommes Energical,"
2. Une phrase presentant ce qu'on propose : equipements pour la maison dans 4 domaines :
{_CATALOG}
3. Terminer par : "Dans quel domaine pouvons-nous vous aider ?"

Ton naturel et commercial, pas robotique. Pas d'emojis."""
        else:
            user_prompt = f"""\
Le client envoie son premier message : "{user_question}"

Accueille-le : "Bonjour, nous sommes Energical, specialiste en chauffage, climatisation, robinetterie et visiophonie."
Ensuite reponds directement a sa demande.

Ce qu'on sait deja : {mem_str}
{"Produits disponibles :\n" + prod_ctx if has_products else "Pose cette question pour affiner : " + (followup_q or "Quel est votre besoin exact ?")}

Pas d'emojis."""

    elif is_discovery_intent(user_question):
        user_prompt = f"""\
Message du client : "{user_question}"
Il veut voir le catalogue complet.
Presente les 4 familles de facon claire :
{_CATALOG}
Termine par : "Laquelle de ces categories vous interesse ?" """

    elif is_followup and has_products:

        # Zoom sur 1 produit precis
        if len(products) == 1:
            p        = products[0]
            nom      = p.get("metadata", {}).get("nom", "ce produit")
            prix     = p.get("metadata", {}).get("prix", "")
            prix_str = f"{prix} DA" if prix and str(prix) not in ("0", "N/A", "") else "Prix non communique"

            user_prompt = f"""\
Message du client : "{user_question}"

Le client demande des informations sur ce produit :
{prod_ctx}

INSTRUCTIONS :
- Reponds uniquement sur "{nom}".
- Donne : nom exact, reference, prix ({prix_str}), disponibilite.
- Decris ses caracteristiques techniques et avantages concrets.
- Explique pourquoi il correspond au profil du client (ce qu'on sait : {mem_str}).
- Maximum 5 lignes.
{('- Termine par : "' + followup_q + '"') if followup_q else '- Ne pose pas de nouvelle question.'}

REGLES ABSOLUES :
- Ne mentionne aucun autre produit.
- Ne fabrique aucune spec inventee.
- Pas d'emojis."""

        elif is_short_memory_answer:
            user_prompt = f"""\
Le client a repondu : "{user_question}" a notre question.

Ce qu'on sait maintenant :
{mem_str}

Produits disponibles :
{prod_ctx}

INSTRUCTIONS :
- Confirme en une phrase que tu as bien pris note.
- Explique brievement comment ca affine le choix.
- Si possible, recommande deja un produit avec une justification courte.
{('- Termine par : "' + followup_q + '"') if followup_q else '- Ne pose pas de nouvelle question.'}

REGLES :
- Ne reliste pas tous les produits depuis le debut.
- Pas d'emojis."""

        else:
            last_rec_str = ""
            if last_recommended:
                rec_nom = last_recommended.get("metadata", {}).get("nom", "")
                if rec_nom:
                    last_rec_str = f"\nDernier produit que tu as recommande : {rec_nom}."

            user_prompt = f"""\
Message du client : "{user_question}"

Produits deja presentes :
{prod_ctx}
{last_rec_str}

Ce qu'on sait du client :
{mem_str}

INSTRUCTIONS :
- "quel est le meilleur / lequel choisir / de quoi tu me conseilles" :
  recommande UN produit avec justification courte basee sur le profil.
- "compare / difference" : compare brievement prix, puissance, usage.
- "plus de details" sans nom precis : donne les details du dernier produit recommande.
- Sois direct, 3 a 5 lignes.
{('- Termine par : "' + followup_q + '"') if followup_q else '- Ne pose pas de nouvelle question.'}

REGLES :
- Utilise uniquement les produits listes ci-dessus.
- Ne change pas de produit recommande sans raison explicite du client.
- Pas d'emojis."""

    elif has_products:
        nb = len(products)
        comparison = ""
        if nb > 1:
            comparison = (
                f"Apres la liste, compare brievement les {nb} produits : "
                "prix, puissance/capacite, usage recommande. "
                "Dis clairement lequel convient a quel besoin.\n"
            )

        followup_line = (
            f'Termine par cette seule question : "{followup_q}"'
            if followup_q
            else "Ne pose pas de question si tu as deja toutes les informations."
        )

        user_prompt = f"""\
Message du client : "{user_question}"
Categorie : {category.upper() if category else "non determinee"}

Ce qu'on sait deja sur le besoin du client :
{mem_str}

PRODUITS DISPONIBLES :
{prod_ctx}

INSTRUCTIONS :
1. Une phrase de confirmation.
2. Presente chaque produit : nom, reference, prix, disponibilite, description utile.
   Numerote, separe par "---".
3. {comparison}4. {followup_line}

REGLES :
- Ne montre QUE les produits listes ci-dessus.
- Ne fabrique aucun produit, prix ou reference.
- Ne pose jamais une question dont la reponse est deja dans "Ce qu'on sait deja".
- Une seule question a la fin.
- Pas d'emojis."""

    elif category and not has_products:
        followup_line = (
            f'Pose cette question : "{followup_q}"'
            if followup_q
            else "Demande si le client peut preciser son besoin."
        )
        user_prompt = f"""\
Message du client : "{user_question}"
Categorie : {category.upper()}
Ce qu'on sait deja : {mem_str}

Aucun produit trouve pour l'instant.
Confirme qu'Energical propose des produits dans cette categorie.
{followup_line}
Ne propose aucun produit invente. Pas d'emojis."""

    elif is_vague_message(user_question):
        user_prompt = f"""\
Message du client : "{user_question}"
Demande poliment ce qu'il recherche parmi les 4 familles Energical :
{_CATALOG}
Une seule question. Pas d'emojis."""

    else:
        user_prompt = f"""\
Message du client : "{user_question}"
Reponds de facon utile et naturelle.
Catalogue Energical : {_CATALOG}
Pas d'emojis."""

    # ---- System prompt ---------------------------------------------------

    system = f"""\
Tu es le conseiller commercial d'Energical Algerie.
Energical est specialiste en equipements pour la maison : chauffage, chauffe-eau, climatisation, robinetterie, visiophonie.

REGLES ABSOLUES :
1. Reponds dans la langue du client (francais, darija algerien, anglais, arabe).
2. Ne pose jamais plus d'UNE question a la fois.
3. N'invente AUCUN produit, prix, reference ou spec technique.
4. Utilise UNIQUEMENT les produits fournis dans le contexte.
5. Ne pose JAMAIS une question dont la reponse est deja connue.
6. Sois naturel, direct, commercial.
7. Si le client parle darija, reponds en darija/francais melange.
8. Jamais d'emojis.
9. Ne change jamais de produit recommande sans raison explicite du client.

GLOSSAIRE DARIJA :
{_GLOSSARY}"""

    # ---- Appel API -------------------------------------------------------

    _throttler.wait_if_needed()
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    for model in _MODELS:
        try:
            resp = groq_client.chat.completions.create(
                model=model,
                temperature=0.3,
                max_tokens=700,
                messages=[
                    {"role": "system",  "content": system},
                    {"role": "user",    "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content

        except RateLimitError:
            time.sleep(2)
            continue
        except Exception as e:
            print(f"[groq_client] Erreur avec {model}: {e}")
            continue

    return "Desole, je suis momentanement indisponible. Veuillez reessayer dans quelques secondes."