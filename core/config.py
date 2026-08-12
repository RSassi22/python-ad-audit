from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Config:
    """Centralise tous les paramètres réglables du projet.
    Modifier un seuil ou une règle se fait ici, pas dans le code métier.
    """
    nb_utilisateurs: int = 200
    seuil_inactivite_jours: int = 90

    departements: List[str] = field(default_factory=lambda: [
        "Finance", "IT", "Marketing", "RH", "Sécurité", "Juridique", "Opérations"
    ])

    groupes_ad: List[str] = field(default_factory=lambda: [
        "Accès_Standard", "Admins_Serveurs", "Accès_Comptabilité",
        "Admins_Domaine", "Accès_RH", "Accès_Serveurs_Bancaires"
    ])

    groupes_sensibles: Dict[str, List[str]] = field(default_factory=lambda: {
        "Admins_Domaine": ["IT", "Sécurité"],
        "Accès_Serveurs_Bancaires": ["IT", "Sécurité", "Opérations"],
        "Admins_Serveurs": ["IT"],
    })

    chemin_export_ad: str = "data/raw/export_ad_fictif.csv"
    chemin_rapport: str = "data/processed/alertes_securite.csv"