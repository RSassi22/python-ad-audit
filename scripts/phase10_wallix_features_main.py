# -*- coding: utf-8 -*-
"""
Phase 10 — Feature engineering des sessions Wallix.

Charge data/wallix_sessions.csv (généré en Phase 9), applique
l'encodage cyclique + le calcul de rareté d'asset par utilisateur,
et sauvegarde le résultat enrichi.

Usage (depuis la racine du projet) :
    python scripts/phase10_wallix_features_main.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.wallix_features import engineer_features, FEATURE_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    root = Path(__file__).resolve().parent.parent
    input_path = root / "data" / "wallix_sessions.csv"
    output_path = root / "data" / "wallix_sessions_features.csv"

    df = pd.read_csv(input_path)
    df = engineer_features(df)
    df.to_csv(output_path, index=False)

    print(f"\n✅ Features générées -> {output_path}")
    print(f"\nColonnes utilisées pour le modèle (FEATURE_COLUMNS) :\n{FEATURE_COLUMNS}")
    print("\nAperçu des nouvelles colonnes :")
    print(df[["requestor_user", "target_asset", "hour", "hour_sin", "hour_cos",
               "asset_rarity_score", "is_anomaly", "anomaly_type"]].head(10).to_string(index=False))

    # Petite vérification utile : les sessions "unusual_asset" doivent avoir
    # un asset_rarity_score globalement plus élevé que la moyenne
    print("\nRareté moyenne de l'asset par type de session :")
    print(df.groupby("anomaly_type")["asset_rarity_score"].mean().round(3))


if __name__ == "__main__":
    main()