import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from .config import Config

logger = logging.getLogger(__name__)


class AuditEngine:
    """Applique les règles de détection sur un jeu de données AD."""

    def __init__(self, config: Config):
        self.config = config

    def detecter_inactifs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retourne les comptes inactifs depuis plus de N jours (défini dans la config)."""
        seuil = datetime.now() - timedelta(days=self.config.seuil_inactivite_jours)
        inactifs = df[df["derniere_connexion"] < seuil].copy()
        inactifs["type_alerte"] = f"Compte inactif > {self.config.seuil_inactivite_jours} jours"
        logger.info(f"{len(inactifs)} comptes inactifs détectés.")
        return inactifs

    def detecter_incoherences(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retourne les comptes dont le groupe AD est incompatible avec le département."""
        def est_incoherent(ligne):
            groupe = ligne["groupe_ad"]
            dept = ligne["departement"]
            if groupe in self.config.groupes_sensibles:
                return dept not in self.config.groupes_sensibles[groupe]
            return False
    

        df = df.copy()
        df["incoherent"] = df.apply(est_incoherent, axis=1)
        incoherences = df[df["incoherent"]].copy()
        incoherences["type_alerte"] = "Incohérence département/groupe"
        logger.info(f"{len(incoherences)} incohérences détectées.")
        return incoherences
    
    def detecter_risques_croises(self, df_ad: pd.DataFrame, df_qualys: pd.DataFrame) -> pd.DataFrame:
        """Croise AD et Qualys : repère les comptes à privilèges élevés
        sur une machine avec une vulnérabilité Critique ou Élevée non patchée.
        """
        groupes_a_privileges = list(self.config.groupes_sensibles.keys())

        # Jointure sur la colonne "id" — équivalent d'un JOIN en SQL
        fusion = df_ad.merge(df_qualys, on="id", how="left")

        condition = (
            fusion["groupe_ad"].isin(groupes_a_privileges)
            & fusion["severite"].isin(["Critique", "Élevée"])
            & (fusion["patch_disponible"] == False)
        )

        risques = fusion[condition].copy()
        risques["type_alerte"] = "Compte à privilèges + machine vulnérable non patchée"
        logger.info(f"{len(risques)} risques croisés AD/Qualys détectés.")
        return risques

    def generer_rapport(self, df: pd.DataFrame) -> pd.DataFrame:
        """Exécute toutes les règles et fusionne les résultats en un seul rapport."""
        colonnes = ["id", "nom", "departement", "groupe_ad", "derniere_connexion", "type_alerte"]

        inactifs = self.detecter_inactifs(df)
        incoherences = self.detecter_incoherences(df)

        rapport = pd.concat([inactifs[colonnes], incoherences[colonnes]], ignore_index=True)
        return rapport

    def sauvegarder_rapport(self, rapport: pd.DataFrame) -> None:
        chemin = Path(self.config.chemin_rapport)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        rapport.to_csv(chemin, index=False)
        logger.info(f"Rapport sauvegardé : {chemin} ({len(rapport)} alertes)")