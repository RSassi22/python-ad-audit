# -*- coding: utf-8 -*-
"""
Phase 9 — Génération des sessions Wallix simulées (baseline + anomalies injectées).
Premier maillon de la chaîne UEBA : phase9 (génère) -> phase10 (features) ->
phase11 (entraîne le modèle + score) -> phase12 (évalue) -> phase13 (charge
tout dans le data warehouse). Chaque script relit le CSV produit par le précédent.

Usage (depuis la racine du projet) :
    python scripts/phase9_wallix_main.py
"""
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.wallix_sources import WallixSimConfig, default_profiles, WallixSessionGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    config = WallixSimConfig()
    profiles = default_profiles()

    generator = WallixSessionGenerator(profiles=profiles, config=config)
    df = generator.generate()

    output_path = Path(__file__).resolve().parent.parent / "data" / "wallix_sessions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"\n✅ {len(df)} sessions générées -> {output_path}")
    print(f"   Anomalies : {df['is_anomaly'].sum()} ({100 * df['is_anomaly'].mean():.1f}%)")
    print("\nRépartition par type d'anomalie :")
    print(df[df["is_anomaly"] == 1]["anomaly_type"].value_counts())
    print("\nAperçu :")
    print(df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()