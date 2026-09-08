# Ce module transforme les alertes "qualitatives" produites par
# core/audit.py (booléens : inactif oui/non, incohérent oui/non...) en UN
# SEUL score chiffré par utilisateur (0 à 10). C'est ce score que consomment
# ensuite core/report.py (rapport PDF), dashboard.py (dashboard Streamlit)
# et scripts/phase13_build_datawarehouse_main.py (entrepôt de données).
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
        # inactifs/incoherences sont les DataFrames déjà calculés par
        # AuditEngine (core/audit.py) — on ne relance pas les règles ici,
        # on se contente de savoir QUELS ids sont concernés.

        poids = self.config.ponderations_risque
        groupes_a_privileges = list(self.config.groupes_sensibles.keys())
        score_max_possible = sum(poids.values())  # calcul dynamique du max théorique

        # Jointure AD + Qualys, comme dans core/audit.py::detecter_risques_croises
        fusion = df_ad.merge(df_qualys, on="id", how="left")

        # Convertir en set (ensemble) rend le test "id in ids_inactifs" très
        # rapide (recherche quasi instantanée), même avec beaucoup d'utilisateurs.
        ids_inactifs = set(inactifs["id"])
        ids_incoherents = set(incoherences["id"])

        def calculer_score_brut(ligne):
            # Score additif : chaque facteur de risque présent ajoute son
            # poids (défini dans Config.ponderations_risque). Un utilisateur
            # peut cumuler plusieurs facteurs à la fois (ex: inactif ET
            # privilégié ET sur une machine vulnérable).
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
        # Le score brut dépend du nombre de règles définies dans la config ;
        # on le ramène toujours sur une échelle fixe de 0 à 10 en le divisant
        # par le score max théorique (somme de tous les poids possibles).
        # Arrondi à 1 décimale pour garder un peu de granularité.
        fusion["score_risque"] = round((fusion["score_brut"] / score_max_possible) * 10, 1)
        fusion["niveau_risque"] = fusion["score_risque"].apply(self._niveau_texte)

        logger.info(f"Scores calculés pour {len(fusion)} utilisateurs.")
        # Tri décroissant : les comptes les plus à risque apparaissent en premier
        # (pratique pour le "Top 10" du rapport PDF et du dashboard).
        return fusion.sort_values("score_risque", ascending=False)

    @staticmethod
    def _niveau_texte(score: int) -> str:
        # Traduit le score chiffré en étiquette lisible (voir le barème
        # dans le README : Faible/Moyen/Élevé/Critique).
        if score >= 8:
            return "Critique"
        elif score >= 5:
            return "Élevé"
        elif score >= 2:
            return "Moyen"
        return "Faible"