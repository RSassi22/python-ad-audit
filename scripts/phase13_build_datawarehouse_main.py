# -*- coding: utf-8 -*-
"""
Phase 13 — Construction du data warehouse SQLite (star schema / constellation)
à partir des deux modules existants (Audit AD + Wallix).

Usage (depuis la racine du projet) :
    python scripts/phase13_build_datawarehouse_main.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.db import get_connection, create_schema, load_ad_audit, load_wallix_sessions  # noqa: E402
from core.config import Config
from core.sources import SourceAD, SourceQualys
from core.audit import AuditEngine
from core.scoring import RiskScorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def build_ad_results() -> pd.DataFrame:
    """Reproduit exactement le pipeline de dashboard.py (charger_donnees())
    pour obtenir le DataFrame `resultats` de l'audit AD."""
    config = Config()

    source_ad = SourceAD(config)
    df_ad = source_ad.generer()

    source_qualys = SourceQualys(config)
    df_qualys = source_qualys.generer(df_ad["id"].tolist())

    moteur = AuditEngine(config)
    inactifs = moteur.detecter_inactifs(df_ad)
    incoherences = moteur.detecter_incoherences(df_ad)

    scorer = RiskScorer(config)
    resultats = scorer.calculer(df_ad, df_qualys, inactifs, incoherences)
    return resultats


def main():
    root = Path(__file__).resolve().parent.parent
    wallix_csv_path = root / "data" / "wallix_sessions_scored.csv"

    conn = get_connection()  # credentials lus depuis .env (voir .env.example)
    create_schema(conn)

    print("Chargement des résultats Audit AD...")
    df_resultats = build_ad_results()
    load_ad_audit(conn, df_resultats)

    print("Chargement des sessions Wallix...")
    df_wallix = pd.read_csv(wallix_csv_path)
    load_wallix_sessions(conn, df_wallix)

    # Petite vérification : compter les lignes de chaque table
    cur = conn.cursor()
    for table in ["dim_user", "dim_asset", "dim_anomaly_type", "dim_time",
                  "fact_ad_audit", "fact_wallix_session"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:22s} : {count} lignes")

    conn.close()
    print("\n✅ Data warehouse PostgreSQL construit avec succès.")


if __name__ == "__main__":
    main()