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
        df["derniere_connexion"] = pd.to_datetime(df["derniere_connexion"])  #  tu utilises les données juste après generer() ou après un charger() depuis un CSV
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


class SourceQualys:
    """Simule un export de scan de vulnérabilités type Qualys, une ligne par utilisateur/machine."""

    def __init__(self, config: Config):
        self.config = config
        self.fake = Faker()

    def generer(self, ids_utilisateurs: list) -> pd.DataFrame:
        """Génère des données de vulnérabilité pour chaque id d'utilisateur fourni.
        On réutilise les mêmes id que ceux d'AD pour pouvoir croiser les deux sources ensuite.
        """
        logger.info("Génération des données Qualys simulées...")

        lignes = []
        for id_utilisateur in ids_utilisateurs:
            a_une_vulnerabilite = random.random() < self.config.proba_vulnerabilite

            if a_une_vulnerabilite:
                lignes.append({
                    "id": id_utilisateur,
                    "machine": f"PC-{id_utilisateur:04d}",
                    "cve": f"CVE-2025-{random.randint(10000, 99999)}",
                    "severite": random.choice(self.config.severites_cve),
                    "patch_disponible": random.choice([True, False]),
                })
            else:
                lignes.append({
                    "id": id_utilisateur,
                    "machine": f"PC-{id_utilisateur:04d}",
                    "cve": None,
                    "severite": None,
                    "patch_disponible": None,
                })

        df = pd.DataFrame(lignes)
        logger.info(f"{df['cve'].notna().sum()} vulnérabilités générées sur {len(df)} machines.")
        return df

    def sauvegarder(self, df: pd.DataFrame) -> None:
        chemin = Path(self.config.chemin_export_qualys)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(chemin, index=False)
        logger.info(f"Export Qualys sauvegardé : {chemin}")

    def charger(self) -> pd.DataFrame:
        chemin = Path(self.config.chemin_export_qualys)
        if not chemin.exists():
            raise FileNotFoundError(f"Fichier introuvable : {chemin}. Lance generer() + sauvegarder() d'abord.")
        return pd.read_csv(chemin)