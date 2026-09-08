# -*- coding: utf-8 -*-
"""
Phase 14 (interne UEBA) — core/wallix_lof_comparison.py

Comparaison LOF vs Isolation Forest.

Ce module NE REDÉFINIT PAS de logique d'évaluation : il réutilise
directement evaluate_global() et evaluate_by_anomaly_type() de
core/wallix_evaluation.py (Phase 5), en les appelant une fois pour
chaque modèle, puis en empilant les résultats côte à côte.

Pourquoi réutiliser plutôt que dupliquer ?
Parce que evaluate_by_anomaly_type() ne dépend que des colonnes
is_anomaly / predicted_anomaly / anomaly_type, qui existent dans le
DataFrame scoré des DEUX modèles (Isolation Forest et LOF produisent
tous les deux ces mêmes colonnes, par construction). Réécrire la même
fonction une seconde fois serait une source de bugs si un jour on
modifie la logique d'évaluation dans wallix_evaluation.py sans penser
à répercuter le changement ici.
"""
import logging

import pandas as pd

from .wallix_model import train_isolation_forest, score_sessions
from .wallix_lof_model import train_and_score_lof
from .wallix_evaluation import evaluate_global, evaluate_by_anomaly_type

logger = logging.getLogger(__name__)


def _build_model_summary(model_name: str, df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction interne (préfixe _ = pas censée être appelée depuis l'extérieur
    de ce fichier) qui assemble, POUR UN SEUL MODÈLE, les métriques globales
    et le recall par type d'anomalie dans un seul petit tableau.

    On repart des deux fonctions déjà existantes dans wallix_evaluation.py
    plutôt que de recalculer quoi que ce soit nous-mêmes.
    """
    # --- Métriques globales (dict simple : precision, recall, f1_score) ---
    global_metrics = evaluate_global(df_scored)

    # On les transforme en une ligne de DataFrame, avec anomaly_type="GLOBAL"
    # pour que cette ligne s'insère proprement dans le même tableau que le
    # détail par type d'anomalie juste après.
    global_row = pd.DataFrame([{
        "anomaly_type": "GLOBAL",
        "recall": global_metrics["recall"],
        "precision": global_metrics["precision"],
        "f1_score": global_metrics["f1_score"],
    }])

    # --- Recall détaillé par type d'anomalie (fonction déjà existante) ---
    # evaluate_by_anomaly_type() renvoie un DataFrame indexé par anomaly_type
    # (total_injected, detected, recall) -> on remet anomaly_type en colonne
    # normale avec reset_index(), pour pouvoir l'empiler avec global_row.
    by_type = evaluate_by_anomaly_type(df_scored).reset_index()
    by_type["precision"] = None  # pas de precision calculée par type ici
    by_type["f1_score"] = None

    # On garde seulement les colonnes communes aux deux tableaux, dans le
    # même ordre, pour pouvoir les empiler proprement avec concat().
    by_type = by_type[["anomaly_type", "recall", "precision", "f1_score"]]

    summary = pd.concat([global_row, by_type], ignore_index=True)
    summary["model"] = model_name
    return summary


def compare_models(df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Entraîne Isolation Forest ET LOF sur les mêmes features, puis compare
    leurs performances (global + par type d'anomalie) dans un seul tableau.

    df_features : DataFrame produit par engineer_features() dans
        core/wallix_features.py. Contient à la fois les colonnes de
        FEATURE_COLUMNS (données aux modèles) ET is_anomaly / anomaly_type
        (utilisées seulement ici, après coup, jamais pendant l'entraînement).

    Retourne un DataFrame avec les colonnes :
        model, anomaly_type, recall, precision, f1_score
    -> une ligne "GLOBAL" + une ligne par type d'anomalie, pour chacun
       des deux modèles (donc 2 x (1 + nb_types_anomalie) lignes au total).
    """
    # --- Isolation Forest (Phase 11, réutilisé tel quel, aucune modif) ---
    iso_model = train_isolation_forest(df_features)
    iso_scored = score_sessions(iso_model, df_features)
    iso_summary = _build_model_summary("Isolation Forest", iso_scored)

    # --- LOF (Phase 14, nouveau) ---
    # Une seule fonction ici (pas train_ puis score_ séparés) : voir le
    # docstring de train_and_score_lof dans wallix_lof_model.py pour
    # l'explication de cette contrainte propre à LOF (novelty=False).
    lof_scored = train_and_score_lof(df_features)
    lof_summary = _build_model_summary("LOF", lof_scored)

    comparison_df = pd.concat([iso_summary, lof_summary], ignore_index=True)
    comparison_df = comparison_df[["model", "anomaly_type", "recall", "precision", "f1_score"]]

    logger.info("Comparaison Isolation Forest vs LOF terminée (%d lignes).", len(comparison_df))
    return comparison_df