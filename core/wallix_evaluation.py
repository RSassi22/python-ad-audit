# -*- coding: utf-8 -*-
"""
Phase 5 (interne UEBA = scripts/phase12_wallix_evaluation_main.py) —
Évaluation du modèle Isolation Forest.

C'est ICI, et seulement ici, qu'on a le droit de comparer les prédictions
du modèle (predicted_anomaly) aux vraies anomalies injectées (is_anomaly).
Le modèle, lui, n'a jamais vu is_anomaly pendant l'entraînement (Phase 4).

Entrée : le DataFrame scoré par core/wallix_model.py. Sortie : des
métriques (dict/DataFrame) affichées en console, et deux images PNG
enregistrées dans docs/screenshots/ (utilisées ensuite dans le README).
"""
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score, confusion_matrix,
    ConfusionMatrixDisplay,
)

logger = logging.getLogger(__name__)


def evaluate_global(df_scored: pd.DataFrame) -> dict:
    """
    Métriques globales : precision, recall, f1-score.

    - precision : parmi tout ce que le modèle a flaggé "anormal", quelle
      proportion l'était vraiment ? (mesure les faux positifs)
    - recall    : parmi toutes les vraies anomalies injectées, quelle
      proportion le modèle a-t-il retrouvée ? (mesure les faux négatifs)
    - f1-score  : moyenne harmonique des deux, résumé équilibré.
    """
    y_true = df_scored["is_anomaly"]
    y_pred = df_scored["predicted_anomaly"]

    metrics = {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }
    logger.info("Métriques globales : %s", {k: round(v, 3) for k, v in metrics.items()})
    return metrics


def evaluate_by_anomaly_type(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Rappel (recall) détaillé PAR TYPE d'anomalie injectée.
    C'est la vue la plus utile : elle dit précisément quel type de
    comportement suspect le modèle sait / ne sait pas encore repérer.
    """
    true_anomalies = df_scored[df_scored["is_anomaly"] == 1].copy()

    summary = (
        true_anomalies
        .groupby("anomaly_type")
        .apply(lambda g: pd.Series({
            "total_injected": len(g),
            "detected": g["predicted_anomaly"].sum(),
            "recall": g["predicted_anomaly"].mean(),
        }))
        .sort_values("recall")
    )
    return summary


def plot_confusion_matrix(df_scored: pd.DataFrame, output_path: Path) -> None:
    """Sauvegarde la matrice de confusion en image."""
    y_true = df_scored["is_anomaly"]
    y_pred = df_scored["predicted_anomaly"]

    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Anomalie"])

    fig, ax = plt.subplots(figsize=(5, 5))
    disp.plot(ax=ax, cmap="Reds", colorbar=False)
    ax.set_title("Matrice de confusion — Isolation Forest")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Matrice de confusion sauvegardée -> %s", output_path)


def plot_score_distribution(df_scored: pd.DataFrame, output_path: Path) -> None:
    """
    Compare la distribution des anomaly_score pour les sessions normales
    vs les vraies anomalies. Visuellement, ça montre si le modèle sépare
    bien les deux populations (idéalement deux courbes peu superposées).
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    normal_scores = df_scored[df_scored["is_anomaly"] == 0]["anomaly_score"]
    anomaly_scores = df_scored[df_scored["is_anomaly"] == 1]["anomaly_score"]

    ax.hist(normal_scores, bins=40, alpha=0.6, label="Sessions normales", color="#333333")
    ax.hist(anomaly_scores, bins=40, alpha=0.7, label="Anomalies injectées", color="#ED1C37")
    ax.set_xlabel("Anomaly score (plus bas = plus suspect)")
    ax.set_ylabel("Nombre de sessions")
    ax.set_title("Distribution des scores d'anomalie")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Distribution des scores sauvegardée -> %s", output_path)