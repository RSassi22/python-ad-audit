# -*- coding: utf-8 -*-
"""
Phase 14 — Comparaison LOF vs Isolation Forest sur les sessions Wallix.

Contrairement à phase12 (qui relit un CSV déjà scoré par Isolation Forest),
ce script repart des données BRUTES et applique lui-même le feature
engineering, car compare_models() a besoin d'entraîner LES DEUX modèles
depuis zéro sur le même DataFrame de features (Isolation Forest ET LOF).

Usage (depuis la racine du projet) :
    python scripts/phase14_lof_main.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.wallix_features import engineer_features
from core.wallix_lof_evaluation import compare_models
from core.wallix_evaluation import plot_score_distribution
from core.wallix_lof_model import train_and_score_lof

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    root = Path(__file__).resolve().parent.parent

    # On repart des données BRUTES (pas du CSV déjà scoré par Isolation
    # Forest), car engineer_features() doit tourner une fois, puis servir
    # de base commune aux deux modèles dans compare_models().
    input_path = root / "data" / "wallix_sessions.csv"
    output_dir = root / "data"
    screenshots_dir = root / "docs" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(input_path)

    # Feature engineering : encodage cyclique de l'heure, score de rareté
    # d'asset, etc. (Phase 10, core/wallix_features.py). Résultat : un seul
    # DataFrame qui contient à la fois FEATURE_COLUMNS (pour les modèles)
    # et is_anomaly/anomaly_type (pour l'évaluation après coup).
    df_features = engineer_features(df_raw)

    # --- Comparaison des deux modèles ---
    print("=== Comparaison Isolation Forest vs LOF ===")
    comparison_df = compare_models(df_features)
    print(comparison_df.round(3).to_string(index=False))

    # On sauvegarde le tableau comparatif en CSV, pour pouvoir le réutiliser
    # tel quel dans le dashboard Streamlit ou le rapport PDF, sans avoir à
    # relancer l'entraînement des modèles à chaque fois.
    comparison_output_path = output_dir / "wallix_lof_vs_isoforest_comparison.csv"
    comparison_df.to_csv(comparison_output_path, index=False)
    print(f"\n✅ Tableau comparatif sauvegardé -> {comparison_output_path}")

    # --- Graphique de distribution des scores, spécifique à LOF ---
    # On réutilise plot_score_distribution() telle quelle (Phase 5), car
    # elle ne dépend que des colonnes anomaly_score / is_anomaly, que LOF
    # produit exactement de la même façon qu'Isolation Forest.
    df_lof_scored = train_and_score_lof(df_features)
    plot_score_distribution(
        df_lof_scored,
        screenshots_dir / "wallix_lof_score_distribution.png",
    )
    print(f"✅ Distribution des scores LOF sauvegardée -> {screenshots_dir}")


if __name__ == "__main__":
    main()