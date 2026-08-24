# -*- coding: utf-8 -*-
"""
Phase 12 — Évaluation du modèle Isolation Forest sur les sessions Wallix.

Usage (depuis la racine du projet) :
    python scripts/phase12_wallix_evaluation_main.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.wallix_evaluation import (
    evaluate_global, evaluate_by_anomaly_type,
    plot_confusion_matrix, plot_score_distribution,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    root = Path(__file__).resolve().parent.parent
    input_path = root / "data" / "wallix_sessions_scored.csv"
    screenshots_dir = root / "docs" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    df_scored = pd.read_csv(input_path)

    print("=== Métriques globales ===")
    global_metrics = evaluate_global(df_scored)
    for name, value in global_metrics.items():
        print(f"  {name:10s} : {value:.3f}")

    print("\n=== Rappel (recall) par type d'anomalie ===")
    by_type = evaluate_by_anomaly_type(df_scored)
    print(by_type.round(3).to_string())

    plot_confusion_matrix(df_scored, screenshots_dir / "wallix_confusion_matrix.png")
    plot_score_distribution(df_scored, screenshots_dir / "wallix_score_distribution.png")

    print(f"\n✅ Graphiques sauvegardés dans {screenshots_dir}")


if __name__ == "__main__":
    main()