# -*- coding: utf-8 -*-
"""
Phase 14 (interne UEBA) — core/wallix_lof_model.py

Entraînement et scoring avec Local Outlier Factor (LOF), en complément
d'Isolation Forest (voir core/wallix_model.py).

Comme Isolation Forest, ce modèle est NON-SUPERVISÉ : il ne voit jamais
is_anomaly / anomaly_type. Ces colonnes ne servent qu'après coup, dans
l'évaluation, pour vérifier si le modèle a bien retrouvé les anomalies
injectées.

Entrée : le même DataFrame de features que pour Isolation Forest
(produit par core/wallix_features.py, colonnes définies dans FEATURE_COLUMNS).

DIFFÉRENCE STRUCTURELLE IMPORTANTE avec wallix_model.py :
Isolation Forest permet de séparer "entraîner" (train_isolation_forest)
et "scorer" (score_sessions) en deux étapes, car le modèle peut ensuite
réutiliser .predict() sur n'importe quelles données.
LOF, lui, est utilisé ici avec novelty=False (voir explication dans le
docstring de train_and_score_lof plus bas) : dans ce mode, sklearn
n'expose PAS de méthode .predict() séparée. La seule façon de l'utiliser
est fit_predict(), qui entraîne ET score en une seule étape, sur le
dataset complet donné d'un coup. C'est pour ça qu'il n'y a ici qu'UNE
seule fonction au lieu de deux : ce n'est pas un oubli, c'est une
contrainte propre à l'algorithme.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from .wallix_features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)


def train_and_score_lof(
    df_features: pd.DataFrame,
    n_neighbors: int = 20,
    contamination: float = 0.04,
) -> pd.DataFrame:
    """
    Entraîne LOF sur les colonnes de FEATURE_COLUMNS et renvoie directement
    le DataFrame enrichi avec le score et la prédiction — en une seule étape.

    n_neighbors : le "k" de LOF, le nombre de voisins utilisés pour calculer
        la densité locale d'un point.
        - Trop petit (ex: 5) -> modèle trop sensible au bruit, il peut
          confondre un point isolé par hasard avec une vraie anomalie.
        - Trop grand (ex: 100) -> le modèle "lisse" trop, il risque de rater
          des anomalies locales fines (l'effet qu'on cherche justement avec LOF).
        20 est la valeur par défaut recommandée dans la doc scikit-learn.

    contamination : même logique que pour Isolation Forest (proportion
        attendue d'anomalies, ici 4% car on l'a injecté nous-mêmes).

    Pourquoi novelty=False (et pas True) ?
        novelty=True servirait si on voulait entraîner LOF sur un jeu de
        données "propre" puis prédire sur de NOUVELLES données plus tard
        (comme le fait Isolation Forest avec predict()).
        Ici, on évalue le modèle sur l'ensemble complet des sessions
        labellisées d'un seul coup (même logique que score_sessions() pour
        Isolation Forest) -> novelty=False + fit_predict() est l'approche
        qui correspond exactement à notre cas d'usage.
    """
    df = df_features.copy()
    X = df[FEATURE_COLUMNS]

    # IMPORTANT (spécifique à LOF, pas nécessaire pour Isolation Forest) :
    # LOF calcule des DISTANCES entre points pour estimer la densité locale.
    # Sans normalisation, une colonne à grande échelle (ex: duration_minutes,
    # qui peut valoir plusieurs centaines) domine complètement le calcul de
    # distance face à des colonnes bornées entre -1 et 1 (hour_sin, hour_cos)
    # ou 0 et 1 (asset_rarity_score). Résultat concret observé en Phase 14 :
    # LOF devenait presque aveugle à l'heure de connexion et à la rareté de
    # l'asset, et ne réagissait quasiment qu'à la durée de session.
    # StandardScaler ramène chaque colonne à une moyenne de 0 et un écart-type
    # de 1, pour que toutes les features pèsent équitablement dans la distance.
    # Isolation Forest n'a PAS ce problème : il fait des coupures aléatoires
    # sur les valeurs, pas des calculs de distance, donc l'échelle des
    # colonnes ne l'affecte pas -> pas besoin de ce scaling dans wallix_model.py.
    X_scaled = StandardScaler().fit_transform(X)

    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        novelty=False,
        n_jobs=-1,  # utilise tous les coeurs CPU dispo, comme pour Isolation Forest
    )

    # fit_predict fait tout en un coup : il apprend la densité locale de
    # chaque zone du dataset ET renvoie directement le verdict (-1 / 1)
    # pour chaque session. On lui donne X_scaled (normalisé), pas X brut.
    raw_predictions = model.fit_predict(X_scaled)

    # negative_outlier_factor_ est l'attribut où sklearn stocke le score,
    # mais en NÉGATIF par convention interne (comme decision_function()
    # pour Isolation Forest : plus c'est bas/négatif, plus c'est suspect).
    # On garde ce même sens ("bas = suspect") pour que anomaly_score reste
    # directement comparable, en un coup d'oeil, à celui d'Isolation Forest.
    df["anomaly_score"] = model.negative_outlier_factor_

    # predict : -1 (anomalie) / 1 (normal) -> on convertit en 0/1, exactement
    # comme dans score_sessions() pour Isolation Forest, pour rester cohérent
    # avec la colonne is_anomaly et pouvoir comparer les deux modèles direct.
    df["predicted_anomaly"] = np.where(raw_predictions == -1, 1, 0)

    n_detected = df["predicted_anomaly"].sum()
    logger.info(
        "LOF entraîné : n_neighbors=%d, contamination=%.2f, %d features. "
        "Sessions marquées anormales : %d / %d",
        n_neighbors, contamination, len(FEATURE_COLUMNS), n_detected, len(df)
    )
    return df