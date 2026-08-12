import logging
import pandas as pd

from .config import Config

logger = logging.getLogger(__name__)


class RiskScorer:
    """Calcule un score de risque combiné (0-10) par utilisateur,
    à partir des données AD et Qualys.
    """

    def __init__(self, config: Config):
        self.config = config

    def calculer(self, df_ad: pd.DataFrame, df_qualys: pd.DataFrame,
                 inactifs: pd.DataFrame, incoherences: pd.DataFrame) -> pd.DataFrame:

        poids = self.config.ponderations_risque
        groupes_a_privileges = list(self.config.groupes_sensibles.keys())
        score_max_possible = sum(poids.values())  # calcul dynamique du max théorique

        fusion = df_ad.merge(df_qualys, on="id", how="left")

        ids_inactifs = set(inactifs["id"])
        ids_incoherents = set(incoherences["id"])

        def calculer_score_brut(ligne):
            score = 0
            if ligne["id"] in ids_inactifs:
                score += poids["inactif"]
            if ligne["id"] in ids_incoherents:
                score += poids["incoherence"]
            if ligne["groupe_ad"] in groupes_a_privileges:
                score += poids["privilege"]
            if ligne["severite"] == "Élevée":
                score += poids["vuln_elevee"]
            if ligne["severite"] == "Critique":
                score += poids["vuln_critique"]
            if ligne["patch_disponible"] == False:
                score += poids["sans_patch"]
            return score

        fusion["score_brut"] = fusion.apply(calculer_score_brut, axis=1)
        # Normalisation sur 10, arrondi à 1 décimale pour garder de la granularité
        fusion["score_risque"] = round((fusion["score_brut"] / score_max_possible) * 10, 1)
        fusion["niveau_risque"] = fusion["score_risque"].apply(self._niveau_texte)

        logger.info(f"Scores calculés pour {len(fusion)} utilisateurs.")
        return fusion.sort_values("score_risque", ascending=False)
    @staticmethod
    def _niveau_texte(score: int) -> str:
        if score >= 8:
            return "Critique"
        elif score >= 5:
            return "Élevé"
        elif score >= 2:
            return "Moyen"
        return "Faible"