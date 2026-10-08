# -*- coding: utf-8 -*-
"""
core/wallix_agent.py

Phase 16 — "Assistant SOC" : génère un résumé en langage naturel d'UNE
session Wallix suspecte, en appelant une API de "grand modèle de langage" (LLM).

Fournisseur utilisé : Groq (https://groq.com), pas Anthropic/Claude. Le
principe de la fonctionnalité est resté le même (Phase 16 initiale), seul le
fournisseur a changé en cours de route, faute de crédits disponibles sur la
clé API Anthropic testée. Groq héberge des modèles ouverts (Llama...) et
propose une API "chat completions" du même style que la plupart des
fournisseurs LLM (OpenAI, Mistral...), donc le code ci-dessous ressemble
volontairement à ce qu'on écrirait avec ces autres API.

Comme core/db.py pour PostgreSQL, la clé API n'est JAMAIS écrite en dur ici :
elle est lue depuis un fichier .env (non committé, voir .gitignore) via
python-dotenv, dans la variable GROQ_API_KEY. Voir .env.example pour le nom
exact de la variable attendue.

Appelé uniquement par core/wallix_dashboard.py, quand l'utilisateur choisit
une session dans le sélecteur et clique sur le bouton "Expliquer cette
session" de l'onglet UEBA.
"""
import logging
import os

import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()  # charge les variables du fichier .env dans l'environnement

# Modèle utilisé pour générer le résumé, centralisé ici en constante plutôt
# qu'en dur dans explain_session() : plus simple à retrouver/changer plus
# tard (le catalogue de modèles disponibles sur Groq évolue régulièrement —
# vérifiable avec client.models.list() si ce modèle venait à disparaître).
# openai/gpt-oss-120b : modèle généraliste "open-weights" de bonne qualité,
# hébergé par Groq, adapté à de la rédaction courte en français.
MODEL_NAME = "openai/gpt-oss-120b"


def _build_prompt(session: pd.Series) -> str:
    """
    Construit le texte envoyé au modèle à partir d'UNE session (une ligne du
    DataFrame scoré, donc une pd.Series : une valeur par colonne).

    Pourquoi lister les colonnes une par une dans le prompt plutôt que de
    dumper toute la ligne brute ? Pour garder le contrôle sur ce qui est
    envoyé à l'API (pas de colonnes techniques inutiles comme session_id) et
    obtenir un prompt lisible, avec des libellés en français plutôt que des
    noms de colonnes bruts type "duration_minutes".
    """
    # .get("colonne", valeur_par_défaut) plutôt que session["colonne"] :
    # évite un crash si jamais une colonne attendue manque (par exemple un
    # CSV généré par une version plus ancienne du pipeline).
    commande_sensible = session.get("triggered_sensitive_command")
    # pd.notna() gère à la fois None et NaN (pandas transforme souvent les
    # valeurs vides en NaN, même dans une colonne censée contenir du texte).
    commande_texte = commande_sensible if pd.notna(commande_sensible) else "aucune"

    return f"""Tu es un analyste SOC (Security Operations Center) qui rédige des notes
d'analyse courtes sur des sessions d'accès privilégié (bastion PAM Wallix).

Voici les caractéristiques d'UNE session détectée comme potentiellement suspecte
par un modèle de détection d'anomalies (UEBA, non-supervisé) :

- Utilisateur : {session.get('requestor_user', 'inconnu')}
- Rôle : {session.get('role', 'inconnu')}
- Machine cible : {session.get('target_asset', 'inconnue')}
- Pays de connexion : {session.get('country', 'inconnu')}
- Heure de connexion : {session.get('hour', 'inconnue')}h
- Durée de la session : {session.get('duration_minutes', 'inconnue')} minutes
- Nombre de commandes exécutées : {session.get('commands_count', 'inconnu')}
- Commande sensible détectée : {commande_texte}
- Type d'anomalie identifié par le modèle : {session.get('anomaly_type', 'non précisé')}
- Score d'anomalie (plus bas = plus suspect) : {session.get('anomaly_score', 'inconnu')}

Rédige un résumé de 3 à 5 phrases, en français, façon note d'analyste SOC :
explique CE QUI est suspect dans cette session et POURQUOI, en te basant
uniquement sur les éléments ci-dessus. Reste factuel, sans jargon technique
inutile, comme si tu expliquais à un collègue qui découvre l'alerte."""


def explain_session(session: pd.Series) -> str:
    """
    Envoie une session au modèle Groq et renvoie son résumé en langage naturel.

    Choix important : cette fonction ne LÈVE jamais d'exception, elle
    renvoie toujours une chaîne de caractères (soit le résumé, soit un
    message d'erreur lisible). Elle est appelée directement depuis le
    dashboard Streamlit (via st.info/st.error) : si elle plantait, un clic
    malheureux sur le bouton "Expliquer cette session" ferait planter tout
    le dashboard, pas juste cette fonctionnalité.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY absente : impossible d'appeler le modèle.")
        return (
            "⚠️ Aucune clé API Groq configurée. Ajoute GROQ_API_KEY "
            "dans le fichier .env à la racine du projet (voir .env.example) "
            "pour activer l'assistant SOC."
        )

    # Import fait À L'INTÉRIEUR de la fonction (pas en haut du fichier) :
    # si le package "groq" n'est pas installé, on veut que SEULE cette
    # fonctionnalité soit indisponible, pas que tout core/wallix_dashboard.py
    # (et donc tout le dashboard, y compris l'onglet Audit AD) plante au
    # démarrage à cause d'un import manquant sur une fonctionnalité optionnelle.
    try:
        import groq
    except ImportError:
        logger.error("Le package 'groq' n'est pas installé.")
        return "⚠️ Le package Python 'groq' n'est pas installé. Lance : pip install groq"

    prompt = _build_prompt(session)

    try:
        client = groq.Groq(api_key=api_key)
        # L'API "chat completions" de Groq suit le même format que la
        # plupart des API de LLM actuelles : on envoie une liste de messages
        # (ici un seul, de rôle "user"), le modèle répond avec un message
        # de rôle "assistant" qu'on va chercher dans response.choices[0].
        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    except groq.AuthenticationError:
        # Levée par le SDK quand la clé API est refusée par le serveur Groq
        # (clé invalide, révoquée, ou expirée) — distincte d'une clé
        # simplement absente (cas géré au-dessus).
        logger.error("Clé API Groq invalide ou expirée.")
        return (
            "⚠️ La clé API Groq configurée est invalide ou expirée. "
            "Vérifie la valeur de GROQ_API_KEY dans .env."
        )
    except groq.APIConnectionError:
        # Levée quand la requête réseau elle-même échoue (pas de réponse du
        # serveur), à distinguer d'une clé refusée ou d'une erreur métier.
        logger.error("Impossible de contacter l'API Groq (problème réseau).")
        return "⚠️ Impossible de contacter l'API Groq. Vérifie ta connexion réseau et réessaie."
    except Exception as exc:
        # Filet de sécurité générique : quota dépassé, modèle retiré du
        # catalogue, service indisponible, etc. On ne liste pas chaque cas
        # un par un, on affiche juste un message clair plutôt que de
        # laisser planter le dashboard sur une erreur non prévue.
        logger.error("Erreur lors de l'appel à l'API Groq : %s", exc)
        return f"⚠️ Erreur lors de l'appel à l'API Groq : {exc}"
