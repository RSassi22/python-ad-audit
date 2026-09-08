# Phase 8 — Dernière étape du pipeline "Audit AD classique" : ajoute la
# génération du rapport PDF (core/report.py) au-dessus du scoring de la
# Phase 7. C'est le script à lancer pour obtenir outputs/rapport_audit.pdf
# (voir aussi le README, section "Générer le rapport PDF").
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.sources import SourceAD, SourceQualys
from core.audit import AuditEngine
from core.scoring import RiskScorer
from core.report import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    config = Config()

    source_ad = SourceAD(config)
    df_ad = source_ad.generer()
    source_ad.sauvegarder(df_ad)

    source_qualys = SourceQualys(config)
    df_qualys = source_qualys.generer(df_ad["id"].tolist())
    source_qualys.sauvegarder(df_qualys)

    moteur = AuditEngine(config)
    inactifs = moteur.detecter_inactifs(df_ad)
    incoherences = moteur.detecter_incoherences(df_ad)

    scorer = RiskScorer(config)
    resultats = scorer.calculer(df_ad, df_qualys, inactifs, incoherences)
    resultats.to_csv(config.chemin_rapport_risque, index=False)

    rapport = ReportGenerator(config)
    rapport.generer(resultats, "outputs/rapport_audit.pdf")

    print(f"\nRapport PDF généré : outputs/rapport_audit.pdf")

if __name__ == "__main__":
    main()