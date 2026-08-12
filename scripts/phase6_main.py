import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.sources import SourceAD, SourceQualys
from core.audit import AuditEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    config = Config()

    # Génération AD
    source_ad = SourceAD(config)
    df_ad = source_ad.generer()
    source_ad.sauvegarder(df_ad)

    # Génération Qualys, en réutilisant les mêmes id que AD
    source_qualys = SourceQualys(config)
    df_qualys = source_qualys.generer(df_ad["id"].tolist())
    source_qualys.sauvegarder(df_qualys)

    # Audit croisé
    moteur = AuditEngine(config)
    risques = moteur.detecter_risques_croises(df_ad, df_qualys)

    print(f"\nTerminé. {len(risques)} comptes à risque élevé détectés (privilèges + vulnérabilité).")
    if len(risques) > 0:
        print(risques[["nom", "departement", "groupe_ad", "machine", "cve", "severite"]].to_string(index=False))

if __name__ == "__main__":
    main()