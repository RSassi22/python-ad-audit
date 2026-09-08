# -*- coding: utf-8 -*-
"""
Phase 13 — Data Warehouse PostgreSQL (schéma en constellation : dimensions
partagées entre deux tables de faits, AD et Wallix).

Dimensions :
  dim_user            -> utilisateur (AD ou Wallix, colonne 'source' pour distinguer)
  dim_asset           -> machine/serveur cible (Wallix uniquement)
  dim_anomaly_type    -> type d'anomalie Wallix (none, unusual_hour, ...)
  dim_time            -> date/heure des sessions Wallix

Faits :
  fact_ad_audit       -> une ligne par compte audité (score de risque AD)
  fact_wallix_session -> une ligne par session Wallix (score d'anomalie)

Les identifiants de connexion NE SONT JAMAIS codés en dur ici : ils sont lus
depuis un fichier .env (non committé) via python-dotenv. Voir .env.example.

NOTE : les identifiants utilisateurs AD (Faker) et Wallix (profils fixes)
ne se recoupent pas naturellement dans les données actuelles — dim_user les
stocke côte à côte avec une colonne `source` plutôt que de prétendre à une
correspondance qui n'existe pas.

Dernier maillon du projet : ce module est appelé uniquement par
scripts/phase13_build_datawarehouse_main.py, qui relance lui-même tout le
pipeline Audit AD (SourceAD/SourceQualys/AuditEngine/RiskScorer) et relit le
CSV Wallix déjà scoré, pour les charger tous les deux dans PostgreSQL. C'est
cette base qui alimente ensuite le fichier Power BI (dashboard_powerbi_ueba.pbix).
"""
import logging
import os
from datetime import datetime

import pandas as pd
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()  # charge les variables du fichier .env dans l'environnement

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS dim_user (
    user_key SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    source TEXT NOT NULL,              -- 'AD' ou 'WALLIX'
    department_or_role TEXT,
    UNIQUE(username, source)
);

CREATE TABLE IF NOT EXISTS dim_asset (
    asset_key SERIAL PRIMARY KEY,
    asset_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_anomaly_type (
    anomaly_type_key SERIAL PRIMARY KEY,
    anomaly_type_label TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_time (
    date_key INTEGER PRIMARY KEY,      -- format AAAAMMJJHH, ex: 2026010110
    full_datetime TIMESTAMP,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hour INTEGER,
    is_weekend INTEGER
);

CREATE TABLE IF NOT EXISTS fact_ad_audit (
    fact_id SERIAL PRIMARY KEY,
    user_key INTEGER NOT NULL REFERENCES dim_user(user_key),
    score_risque REAL,
    niveau_risque TEXT
);

CREATE TABLE IF NOT EXISTS fact_wallix_session (
    fact_id SERIAL PRIMARY KEY,
    session_id TEXT,
    user_key INTEGER NOT NULL REFERENCES dim_user(user_key),
    asset_key INTEGER NOT NULL REFERENCES dim_asset(asset_key),
    date_key INTEGER NOT NULL REFERENCES dim_time(date_key),
    anomaly_type_key INTEGER NOT NULL REFERENCES dim_anomaly_type(anomaly_type_key),
    duration_minutes REAL,
    commands_count INTEGER,
    risk_flag INTEGER,
    anomaly_score REAL,
    is_anomaly INTEGER,
    predicted_anomaly INTEGER
);
"""


def get_connection():
    """Connexion PostgreSQL, credentials lus depuis les variables d'environnement (.env)."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "python_ad_audit_dwh"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD"),
    )


def create_schema(conn) -> None:
    cur = conn.cursor()
    cur.execute(SCHEMA_DDL)
    conn.commit()
    logger.info("Schéma créé (4 dimensions + 2 faits).")


# ---------------------------------------------------------------- #
# Fonctions "get_or_create" : évitent les doublons dans les dimensions
# en réutilisant la clé existante si la valeur est déjà présente.
# Note : PostgreSQL utilise %s comme placeholder (pas ? comme SQLite).
# ---------------------------------------------------------------- #
def _get_or_create_user(conn, username: str, source: str, department_or_role: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT user_key FROM dim_user WHERE username = %s AND source = %s", (username, source))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_user (username, source, department_or_role) VALUES (%s, %s, %s) RETURNING user_key",
        (username, source, department_or_role),
    )
    return cur.fetchone()[0]


def _get_or_create_asset(conn, asset_name: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT asset_key FROM dim_asset WHERE asset_name = %s", (asset_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO dim_asset (asset_name) VALUES (%s) RETURNING asset_key", (asset_name,))
    return cur.fetchone()[0]


def _get_or_create_anomaly_type(conn, label: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT anomaly_type_key FROM dim_anomaly_type WHERE anomaly_type_label = %s", (label,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_anomaly_type (anomaly_type_label) VALUES (%s) RETURNING anomaly_type_key",
        (label,),
    )
    return cur.fetchone()[0]


def _get_or_create_time(conn, dt: datetime) -> int:
    date_key = int(dt.strftime("%Y%m%d%H"))
    cur = conn.cursor()
    cur.execute("SELECT date_key FROM dim_time WHERE date_key = %s", (date_key,))
    if cur.fetchone():
        return date_key
    cur.execute(
        "INSERT INTO dim_time (date_key, full_datetime, year, month, day, hour, is_weekend) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (date_key, dt, dt.year, dt.month, dt.day, dt.hour, int(dt.weekday() >= 5)),
    )
    return date_key


# ---------------------------------------------------------------- #
# Chargement (ETL) des deux sources
# ---------------------------------------------------------------- #
def load_ad_audit(conn, df_resultats: pd.DataFrame) -> None:
    """Charge le DataFrame `resultats` du module Audit AD (voir dashboard.py)."""
    n = 0
    for _, row in df_resultats.iterrows():
        user_key = _get_or_create_user(conn, row["nom"], "AD", row["departement"])
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO fact_ad_audit (user_key, score_risque, niveau_risque) VALUES (%s, %s, %s)",
            (user_key, float(row["score_risque"]), row["niveau_risque"]),
        )
        n += 1
    conn.commit()
    logger.info("fact_ad_audit : %d lignes chargées", n)


def load_wallix_sessions(conn, df_scored: pd.DataFrame) -> None:
    """Charge le CSV data/wallix_sessions_scored.csv (sortie de la Phase 4/5)."""
    n = 0
    for _, row in df_scored.iterrows():
        user_key = _get_or_create_user(conn, row["requestor_user"], "WALLIX", row["role"])
        asset_key = _get_or_create_asset(conn, row["target_asset"])
        anomaly_type_key = _get_or_create_anomaly_type(conn, row["anomaly_type"])
        dt = pd.to_datetime(row["start_time"]).to_pydatetime()
        date_key = _get_or_create_time(conn, dt)

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO fact_wallix_session
                (session_id, user_key, asset_key, date_key, anomaly_type_key,
                 duration_minutes, commands_count, risk_flag,
                 anomaly_score, is_anomaly, predicted_anomaly)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row["session_id"], user_key, asset_key, date_key, anomaly_type_key,
                float(row["duration_minutes"]), int(row["commands_count"]), int(row["risk_flag"]),
                float(row["anomaly_score"]), int(row["is_anomaly"]), int(row["predicted_anomaly"]),
            ),
        )
        n += 1
    conn.commit()
    logger.info("fact_wallix_session : %d lignes chargées", n)