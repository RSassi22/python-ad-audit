import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datetime import datetime, timedelta
from core.config import Config
from core.audit import AuditEngine


def test_detecter_inactifs_identifie_bien_les_comptes_anciens():
    """Un compte dont la dernière connexion date de plus de 90 jours doit être détecté."""
    config = Config()
    moteur = AuditEngine(config)

    date_ancienne = datetime.now() - timedelta(days=120)  # 120 jours > seuil de 90
    date_recente = datetime.now() - timedelta(days=10)    # 10 jours < seuil

    df = pd.DataFrame([
        {"id": 1, "nom": "Compte Inactif", "departement": "IT",
         "groupe_ad": "Accès_Standard", "derniere_connexion": date_ancienne},
        {"id": 2, "nom": "Compte Actif", "departement": "IT",
         "groupe_ad": "Accès_Standard", "derniere_connexion": date_recente},
    ])

    resultat = moteur.detecter_inactifs(df)

    assert len(resultat) == 1
    assert resultat.iloc[0]["nom"] == "Compte Inactif"


def test_detecter_incoherences_repere_groupe_sensible_hors_departement():
    """Un compte Marketing avec un accès Admins_Domaine doit être signalé incohérent."""
    config = Config()
    moteur = AuditEngine(config)

    df = pd.DataFrame([
        {"id": 1, "nom": "Cas Incohérent", "departement": "Marketing", "groupe_ad": "Admins_Domaine"},
        {"id": 2, "nom": "Cas Cohérent", "departement": "IT", "groupe_ad": "Admins_Domaine"},
    ])

    resultat = moteur.detecter_incoherences(df)

    assert len(resultat) == 1
    assert resultat.iloc[0]["nom"] == "Cas Incohérent"


def test_detecter_incoherences_ignore_groupe_non_sensible():
    """Un groupe qui n'est pas dans la liste des groupes sensibles ne doit jamais être signalé."""
    config = Config()
    moteur = AuditEngine(config)

    df = pd.DataFrame([
        {"id": 1, "nom": "Cas Standard", "departement": "Marketing", "groupe_ad": "Accès_Standard"},
    ])

    resultat = moteur.detecter_incoherences(df)

    assert len(resultat) == 0