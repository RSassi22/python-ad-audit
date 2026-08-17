import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from core.config import Config
from core.scoring import RiskScorer


def test_score_augmente_avec_le_cumul_de_facteurs_de_risque():
    """Un compte cumulant plusieurs facteurs de risque doit avoir un score plus élevé
    qu'un compte n'en cumulant qu'un seul.
    """
    config = Config()
    scorer = RiskScorer(config)

    df_ad = pd.DataFrame([
        {"id": 1, "nom": "Risque Élevé", "departement": "IT", "groupe_ad": "Admins_Domaine"},
        {"id": 2, "nom": "Risque Faible", "departement": "IT", "groupe_ad": "Accès_Standard"},
    ])
    df_qualys = pd.DataFrame([
        {"id": 1, "machine": "PC-0001", "cve": "CVE-2025-00001", "severite": "Critique", "patch_disponible": False},
        {"id": 2, "machine": "PC-0002", "cve": None, "severite": None, "patch_disponible": None},
    ])

    inactifs_vide = pd.DataFrame(columns=["id"])
    incoherences_vide = pd.DataFrame(columns=["id"])

    resultats = scorer.calculer(df_ad, df_qualys, inactifs_vide, incoherences_vide)

    score_eleve = resultats[resultats["id"] == 1]["score_risque"].iloc[0]
    score_faible = resultats[resultats["id"] == 2]["score_risque"].iloc[0]

    assert score_eleve > score_faible


def test_score_ne_depasse_jamais_dix():
    """Peu importe le nombre de facteurs cumulés, le score ne doit jamais dépasser 10."""
    config = Config()
    scorer = RiskScorer(config)

    df_ad = pd.DataFrame([
        {"id": 1, "nom": "Pire Cas Possible", "departement": "IT", "groupe_ad": "Admins_Domaine"},
    ])
    df_qualys = pd.DataFrame([
        {"id": 1, "machine": "PC-0001", "cve": "CVE-2025-00001", "severite": "Critique", "patch_disponible": False},
    ])
    inactifs = pd.DataFrame([{"id": 1}])
    incoherences = pd.DataFrame([{"id": 1}])

    resultats = scorer.calculer(df_ad, df_qualys, inactifs, incoherences)

    assert resultats.iloc[0]["score_risque"] <= 10