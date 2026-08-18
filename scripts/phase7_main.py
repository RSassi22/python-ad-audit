import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.sources import SourceAD, SourceQualys
from core.audit import AuditEngine
from core.scoring import RiskScorer

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

    chemin_sortie = Path(config.chemin_rapport_risque)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    resultats.to_csv(chemin_sortie, index=False)

    print(f"\nTop 10 des comptes à risque :")
    print(resultats[["nom", "departement", "groupe_ad", "score_risque", "niveau_risque"]].head(10).to_string(index=False))
    print(f"\nRapport complet sauvegardé : {chemin_sortie}")

if __name__ == "__main__":
    main() 


    # Qualiys threats 