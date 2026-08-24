# -*- coding: utf-8 -*-
"""
Phase 6 — Vue Streamlit "Sessions à risque" pour le module Wallix.

Ce module expose UNE seule fonction, render_wallix_dashboard(), pensée
pour être appelée depuis dashboard.py sans dépendre de sa structure interne
(onglets, sidebar...). Il suffit de l'importer et de l'appeler où tu veux.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "wallix_sessions_scored.csv"


@st.cache_data
def _load_scored_sessions() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["start_time"])
    return df


def render_wallix_dashboard() -> None:
    """Affiche la vue complète 'Sessions Wallix à risque'. À appeler depuis dashboard.py."""

    if not DATA_PATH.exists():
        st.warning(
            "Aucune donnée trouvée. Lance d'abord les scripts des phases 9 à 12 "
            "(génération -> features -> modèle -> évaluation) pour produire "
            f"`{DATA_PATH.name}`."
        )
        return

    df = _load_scored_sessions()

    st.subheader("🛡️ Détection d'anomalies — Sessions privilégiées Wallix")
    st.caption(
        "Score produit par un modèle Isolation Forest (scikit-learn), non-supervisé, "
        "entraîné sur le comportement historique de chaque utilisateur/entité (logique UEBA)."
    )

    # ---------------------------------------------------------------- KPIs
    total_sessions = len(df)
    n_flagged = int(df["predicted_anomaly"].sum())
    detection_rate = n_flagged / total_sessions if total_sessions else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions totales", f"{total_sessions:,}")
    col2.metric("Sessions signalées suspectes", f"{n_flagged}")
    col3.metric("Taux de signalement", f"{detection_rate:.1%}")

    st.divider()

    # ---------------------------------------------------------------- Filtres
    col_a, col_b = st.columns(2)
    with col_a:
        users = ["Tous"] + sorted(df["requestor_user"].unique().tolist())
        selected_user = st.selectbox("Filtrer par utilisateur", users)
    with col_b:
        show_only_flagged = st.checkbox("Afficher uniquement les sessions signalées", value=True)

    df_filtered = df.copy()
    if selected_user != "Tous":
        df_filtered = df_filtered[df_filtered["requestor_user"] == selected_user]
    if show_only_flagged:
        df_filtered = df_filtered[df_filtered["predicted_anomaly"] == 1]

    # ---------------------------------------------------------------- Tableau
    df_display = df_filtered.sort_values("anomaly_score").copy()
    df_display["Suspicion"] = df_display["predicted_anomaly"].map(
        {1: "🔴 Suspecte", 0: "🟢 Normale"}
    )

    st.dataframe(
        df_display[[
            "session_id", "requestor_user", "role", "target_asset", "protocol",
            "start_time", "duration_minutes", "commands_count",
            "anomaly_score", "Suspicion",
        ]].rename(columns={
            "session_id": "ID Session", "requestor_user": "Utilisateur",
            "role": "Rôle", "target_asset": "Asset cible", "protocol": "Protocole",
            "start_time": "Début", "duration_minutes": "Durée (min)",
            "commands_count": "Nb commandes", "anomaly_score": "Score",
        }),
        use_container_width=True,
        height=400,
    )

    st.divider()

    # ---------------------------------------------------------------- Distribution des scores
    st.markdown("**Distribution des scores d'anomalie**")
    st.caption("Plus le score est bas, plus la session est jugée suspecte par le modèle.")

    # IMPORTANT : on n'utilise PAS value_counts(bins=...) ici.
    # Cette méthode retourne un index de type pandas.Interval, que Streamlit
    # ne sait pas afficher proprement sur l'axe d'un bar_chart (il l'affiche
    # comme un objet brut {"left": ..., "right": ...}, illisible).
    # À la place : on calcule l'histogramme nous-mêmes avec numpy, et on
    # utilise le CENTRE de chaque tranche (un simple float) comme label.
    import numpy as np

    counts, bin_edges = np.histogram(df["anomaly_score"], bins=30)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    histogram_df = pd.DataFrame({
        "score": [round(c, 3) for c in bin_centers],
        "nombre_de_sessions": counts,
    }).set_index("score")

    st.bar_chart(histogram_df)