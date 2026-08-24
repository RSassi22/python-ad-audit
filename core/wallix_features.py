# -*- coding: utf-8 -*-
"""
Feature engineering pour la détection d'anomalies (Phase 3).

Objectif : transformer les logs bruts de sessions Wallix en variables
numériques exploitables par Isolation Forest, en respectant la logique
UEBA (comportement évalué PAR RAPPORT au profil de chaque utilisateur,
pas dans l'absolu).

IMPORTANT (data leakage) :
Les colonnes `is_anomaly` et `anomaly_type` ne sont JAMAIS utilisées comme
features. Elles sont conservées à part, uniquement pour évaluer la
performance du modèle après coup (Phase 5). Isolation Forest est
non-supervisé : il ne doit jamais "voir" ces colonnes pendant l'entraînement.
"""
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Colonnes numériques qui seront effectivement passées au modèle ML.
# Centralisé ici pour que Phase 4 (entraînement du modèle) importe
# directement cette liste plutôt que de la redéfinir.
FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "is_weekend",
    "duration_minutes",
    "commands_count",
    "asset_rarity_score",
    "risk_flag",
]


def _encode_hour_cyclic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforme l'heure (0-23) en coordonnées sur un cercle trigonométrique.
    Pourquoi : sans ça, le modèle croit que 23h et 0h sont très éloignées
    (distance brute = 23) alors qu'elles ne sont séparées que d'1 heure.
    """
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    return df


def _compute_asset_rarity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule, POUR CHAQUE UTILISATEUR, à quelle fréquence il utilise
    habituellement l'asset de la session en cours.

    asset_rarity_score = 1 - fréquence_historique(user, asset)
      -> proche de 0 : asset que cet utilisateur touche très souvent
      -> proche de 1 : asset que cet utilisateur n'a (presque) jamais touché

    C'est LA feature la plus directement liée à la logique UEBA : elle est
    relative à chaque profil, pas à une moyenne globale.
    """
    # Nombre de sessions par (utilisateur, asset)
    user_asset_counts = df.groupby(["requestor_user", "target_asset"]).size()
    # Nombre total de sessions par utilisateur
    user_totals = df.groupby("requestor_user").size()

    # Fréquence relative : combien de fois (en %) cet utilisateur va sur CET asset
    freq = user_asset_counts / user_totals
    freq_lookup = freq.to_dict()  # clé = (user, asset) -> fréquence

    def rarity_for_row(row):
        key = (row["requestor_user"], row["target_asset"])
        frequence_habituelle = freq_lookup.get(key, 0.0)
        return 1.0 - frequence_habituelle

    df["asset_rarity_score"] = df.apply(rarity_for_row, axis=1)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Point d'entrée principal : prend le DataFrame brut (sortie de
    WallixSessionGenerator.generate()) et retourne le même DataFrame
    enrichi des colonnes numériques prêtes pour le ML.

    Les colonnes originales (requestor_user, target_asset, is_anomaly...)
    sont conservées pour la lisibilité et l'évaluation future — seules
    les colonnes listées dans FEATURE_COLUMNS seront passées au modèle.
    """
    df = df.copy()

    df = _encode_hour_cyclic(df)
    df = _compute_asset_rarity(df)

    # risk_flag est déjà numérique (0/1), duration_minutes et commands_count aussi
    # -> rien à transformer de plus pour ces colonnes

    logger.info("Features générées : %s", FEATURE_COLUMNS)
    return df


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne uniquement les colonnes numériques destinées au modèle
    (celles listées dans FEATURE_COLUMNS), dans l'ordre attendu."""
    return df[FEATURE_COLUMNS]