# Ce fichier est le "panneau de contrôle" du module Audit AD (pas du module
# Wallix/UEBA, qui a sa propre config autonome dans wallix_sources.py).
# Tous les autres fichiers de core/ et scripts/phase*.py importent la classe
# Config ci-dessous et lisent leurs paramètres dedans, au lieu d'avoir des
# valeurs codées en dur un peu partout. Résultat concret : pour changer le
# nombre d'utilisateurs générés ou le seuil d'inactivité, on modifie une
# seule ligne ici, et tout le pipeline (sources -> audit -> scoring -> report)
# en tient compte automatiquement.
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Config:
    """Centralise tous les paramètres réglables du projet.
    Modifier un seuil ou une règle se fait ici, pas dans le code métier.
    """
    # Nombre de faux utilisateurs AD à générer (utilisé par core/sources.py::SourceAD.generer)
    nb_utilisateurs: int = 200
    # Un compte dont la dernière connexion dépasse ce nombre de jours est
    # considéré "inactif" par core/audit.py::AuditEngine.detecter_inactifs
    seuil_inactivite_jours: int = 90

    # Départements possibles pour un utilisateur fictif (tirage aléatoire dans sources.py)
    departements: List[str] = field(default_factory=lambda: [
        "Finance", "IT", "Marketing", "RH", "Sécurité", "Juridique", "Opérations"
    ])

    # Groupes AD possibles pour un utilisateur fictif (tirage aléatoire dans sources.py)
    groupes_ad: List[str] = field(default_factory=lambda: [
        "Accès_Standard", "Admins_Serveurs", "Accès_Comptabilité",
        "Admins_Domaine", "Accès_RH", "Accès_Serveurs_Bancaires"
    ])

    # Règle métier : pour chaque groupe "sensible", la liste des départements
    # où son attribution est normale. Un utilisateur qui a ce groupe mais
    # est dans un AUTRE département déclenche une "incohérence"
    # (voir core/audit.py::detecter_incoherences).
    groupes_sensibles: Dict[str, List[str]] = field(default_factory=lambda: {
        "Admins_Domaine": ["IT", "Sécurité"],
        "Accès_Serveurs_Bancaires": ["IT", "Sécurité", "Opérations"],
        "Admins_Serveurs": ["IT"],
    })

    # Poids attribué à chaque facteur de risque quand core/scoring.py calcule
    # le score final (0-10) d'un utilisateur. Plus un poids est élevé, plus
    # ce facteur pèse lourd dans le score. La somme de ces poids sert aussi
    # de "score max théorique" pour normaliser sur 10 (voir scoring.py).
    ponderations_risque: Dict[str, int] = field(default_factory=lambda: {
        "inactif": 2,
        "incoherence": 3,
        "privilege": 2,
        "vuln_elevee": 3,
        "vuln_critique": 5,
        "sans_patch": 2,
    })

    # Chemins des fichiers CSV utilisés pour faire communiquer les modules
    # entre eux : un module écrit le CSV, le suivant le relit (voir les
    # scripts scripts/phase*.py pour l'enchaînement complet).
    chemin_export_ad: str = "data/raw/export_ad_fictif.csv"
    chemin_rapport: str = "data/processed/alertes_securite.csv"

    # Paramètres de la simulation Qualys (voir core/sources.py::SourceQualys)
    severites_cve: List[str] = field(default_factory=lambda: ["Faible", "Moyenne", "Élevée", "Critique"])
    proba_vulnerabilite: float = 0.35  # 35% de chances qu'une machine ait une vulnérabilité

    chemin_export_qualys: str = "data/raw/export_qualys_fictif.csv"
    # Sortie finale du scoring (core/scoring.py) : un score de risque par utilisateur.
    # C'est ce fichier que lit ensuite le dashboard / le rapport PDF.
    chemin_rapport_risque: str = "data/processed/scores_risque.csv"