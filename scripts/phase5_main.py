import logging
import sys
from pathlib import Path

# Permet d'importer le package "core" même si ce script est dans scripts/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.sources import SourceAD
from core.audit import AuditEngine

# Configuration du logging : affiche l'heure, le niveau, et le message 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    config = Config()

    source = SourceAD(config)
    df = source.generer()
    source.sauvegarder(df)

    df_charge = source.charger()

    moteur = AuditEngine(config)
    rapport = moteur.generer_rapport(df_charge)
    moteur.sauvegarder_rapport(rapport)

    print(f"\nTerminé. {len(rapport)} alertes générées dans {config.chemin_rapport}")

if __name__ == "__main__":
    main()



    #  phase 5 