import logging
from pathlib import Path
import pandas as pd
from faker import Faker
import random

from .config import Config

logger = logging.getLogger(__name__)


class SourceAD:
    """Représente une source de données Active Directory (générée ou chargée depuis un fichier)."""

    def __init__(self, config: Config):
        self.config = config
        self.fake = Faker()

    def generer(self) -> pd.DataFrame:
        """Génère un jeu de données AD fictif selon les paramètres de la config."""
        logger.info(f"Génération de {self.config.nb_utilisateurs} utilisateurs fictifs...")

        utilisateurs = []
        for i in range(self.config.nb_utilisateurs):
            utilisateurs.append({
                "id": i + 1,
                "nom": self.fake.name(),
                "departement": random.choice(self.config.departements),
                "groupe_ad": random.choice(self.config.groupes_ad),
                "derniere_connexion": self.fake.date_between(start_date="-180d", end_date="today")
            })

        df = pd.DataFrame(utilisateurs)
        logger.info(f"{len(df)} utilisateurs générés avec succès.")
        return df

    def sauvegarder(self, df: pd.DataFrame) -> None:
        """Sauvegarde le DataFrame en CSV, en créant le dossier parent si besoin."""
        chemin = Path(self.config.chemin_export_ad)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(chemin, index=False)
        logger.info(f"Export sauvegardé : {chemin}")

    def charger(self) -> pd.DataFrame:
        """Charge les données AD depuis le CSV. Lève une erreur claire si le fichier est absent."""
        chemin = Path(self.config.chemin_export_ad)
        if not chemin.exists():
            raise FileNotFoundError(
                f"Fichier introuvable : {chemin}. Lance d'abord generer() + sauvegarder()."
            )
        df = pd.read_csv(chemin)
        df["derniere_connexion"] = pd.to_datetime(df["derniere_connexion"])
        logger.info(f"{len(df)} utilisateurs chargés depuis {chemin}.")
        return df