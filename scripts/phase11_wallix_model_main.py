# -*- coding: utf-8 -*-
"""
Phase 11 — Entraînement + scoring Isolation Forest sur les sessions Wallix.

Usage (depuis la racine du projet) :
    python scripts/phase11_wallix_model_main.py

Note : ce script donne un premier aperçu rapide des résultats. L'évaluation
rigoureuse (précision/rappel vs anomalies injectées) est faite en Phase 5.
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.wallix_model import train_isolation_forest, score_sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    root = Path(__file__).resolve().parent.parent
    input_path = root / "data" / "wallix_sessions_features.csv"
    output_path = root / "data" / "wallix_sessions_scored.csv"

    df_features = pd.read_csv(input_path)

    model = train_isolation_forest(df_features, contamination=0.04)
    df_scored = score_sessions(model, df_features)

    df_scored.to_csv(output_path, index=False)
    print(f"\n✅ Sessions scorées -> {output_path}")

    # Aperçu rapide : les sessions jugées les PLUS suspectes par le modèle
    print("\nTop 10 des sessions les plus suspectes (score le plus bas = le plus anormal) :")
    top_suspicious = df_scored.sort_values("anomaly_score").head(10)
    print(top_suspicious[[
        "session_id", "requestor_user", "target_asset", "hour",
        "anomaly_score", "predicted_anomaly", "is_anomaly", "anomaly_type"
    ]].to_string(index=False))

    # Coup d'oeil rapide : parmi les vraies anomalies injectées, combien
    # le modèle en a-t-il retrouvé ? (évaluation détaillée en Phase 5)
    true_anomalies = df_scored[df_scored["is_anomaly"] == 1]
    detected = true_anomalies[true_anomalies["predicted_anomaly"] == 1]
    print(f"\nAperçu rapide : {len(detected)} / {len(true_anomalies)} "
          f"vraies anomalies retrouvées par le modèle.")


if __name__ == "__main__":
    main()