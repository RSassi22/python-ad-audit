# Phase 5 — Premier script à utiliser le package core/ (au lieu de logique
# codée en dur comme dans phase1-4). À partir d'ici, tout le code métier
# vit dans core/ et les scripts scripts/phaseN_*.py ne font plus
# qu'ORCHESTRER ces briques (les appeler dans le bon ordre) : c'est le
# même schéma que réutilisent phase6, phase7, phase8 et phase13.
import logging
import sys
from pathlib import Path

# Ce script est exécuté depuis scripts/, mais core/ est un dossier frère
# (à la racine du projet). sys.path.append ajoute la racine du projet à la
# liste des dossiers où Python cherche les modules, ce qui rend
# "from core.xxx import ..." possible ci-dessous. Tous les autres scripts
# scripts/phaseN_*.py font exactement la même chose en première ligne.
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
    config = Config()  # tous les paramètres du pipeline viennent d'ici

    source = SourceAD(config)
    df = source.generer()
    source.sauvegarder(df)  # écrit data/raw/export_ad_fictif.csv

    # Ce rechargement est volontaire : il vérifie que le CSV qu'on vient
    # d'écrire est bien relisible tel quel (aller-retour disque complet),
    # plutôt que de continuer à travailler avec `df` déjà en mémoire.
    df_charge = source.charger()

    moteur = AuditEngine(config)
    rapport = moteur.generer_rapport(df_charge)
    moteur.sauvegarder_rapport(rapport)  # écrit data/processed/alertes_securite.csv

    print(f"\nTerminé. {len(rapport)} alertes générées dans {config.chemin_rapport}")

if __name__ == "__main__":
    main()