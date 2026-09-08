# -*- coding: utf-8 -*-
"""
Phase 4 (interne UEBA = scripts/phase11_wallix_model_main.py) — Entraînement
du modèle Isolation Forest sur les features Wallix.

Le modèle est NON-SUPERVISÉ : il ne voit jamais is_anomaly / anomaly_type
pendant l'entraînement. Ces colonnes ne servent qu'après coup, en Phase 5,
pour évaluer si le modèle a bien retrouvé les anomalies qu'on avait injectées.

Entrée : le DataFrame de features produit par core/wallix_features.py.
Sortie (score_sessions) : le DataFrame enrichi d'un score d'anomalie,
consommé par core/wallix_evaluation.py, core/wallix_dashboard.py et
scripts/phase13_build_datawarehouse_main.py.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .wallix_features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)


def train_isolation_forest(
    df_features: pd.DataFrame,
    n_estimators: int = 200,
    contamination: float = 0.04,
    random_state: int = 42,
) -> IsolationForest:
    """
    Entraîne un Isolation Forest sur les colonnes numériques définies
    dans FEATURE_COLUMNS.

    contamination : proportion attendue d'anomalies. Ici on la connaît
    (on a injecté 4% nous-mêmes) -> pratique pour valider l'approche.
    En conditions réelles, ce chiffre est une estimation métier, pas une
    vérité mesurée.
    """
    X = df_features[FEATURE_COLUMNS]

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,  # utilise tous les coeurs CPU dispo -> entraînement plus rapide
    )
    model.fit(X)

    logger.info(
        "Isolation Forest entraîné : %d arbres, contamination=%.2f, %d features",
        n_estimators, contamination, len(FEATURE_COLUMNS)
    )
    return model


def score_sessions(model: IsolationForest, df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le modèle entraîné sur les données et enrichit le DataFrame
    avec les résultats :
      - anomaly_score : score continu (plus c'est BAS/négatif, plus c'est suspect)
      - predicted_anomaly : 1 si le modèle juge la session anormale, 0 sinon
    """
    df = df_features.copy()
    X = df[FEATURE_COLUMNS]

    # decision_function : score continu, négatif = anormal, positif = normal
    df["anomaly_score"] = model.decision_function(X)

    # predict : -1 (anomalie) / 1 (normal) -> on convertit en 0/1 pour rester
    # cohérent avec notre colonne is_anomaly (plus lisible pour la suite)
    raw_predictions = model.predict(X)
    df["predicted_anomaly"] = np.where(raw_predictions == -1, 1, 0)

    n_detected = df["predicted_anomaly"].sum()
    logger.info("Sessions marquées anormales par le modèle : %d / %d", n_detected, len(df))
    return df