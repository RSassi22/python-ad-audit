# Point d'entrée de l'application Streamlit (lancée via `streamlit run dashboard.py`).
# C'est la "vitrine" du projet : il réutilise telles quelles les briques de
# core/ (les mêmes que scripts/phase7_main.py) pour l'onglet Audit AD, et
# délègue l'onglet Wallix à core/wallix_dashboard.py. Aucune logique de
# détection/scoring n'est réécrite ici : ce fichier ne fait qu'orchestrer
# l'affichage (KPIs, filtres, graphiques, tableau).
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd

from core.config import Config
from core.sources import SourceAD, SourceQualys
from core.audit import AuditEngine
from core.scoring import RiskScorer
from core.wallix_dashboard import render_wallix_dashboard

# --- Configuration de la page ---
st.set_page_config(page_title="Audit AD - Dashboard", layout="wide")

# --- Cache : évite de régénérer les données à chaque interaction utilisateur ---
# @st.cache_data mémorise le résultat de la fonction : Streamlit relance TOUT
# le script à chaque clic (changement de filtre, etc.), donc sans ce cache,
# on regénérerait des données AD/Qualys aléatoires différentes à chaque clic.
@st.cache_data
def charger_donnees():
    # Reproduit exactement le même enchaînement que scripts/phase7_main.py :
    # génération AD -> génération Qualys -> détection -> scoring.
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

# --- Titre global ---
st.title("🔒 Dashboard Sécurité — Active Directory & Sessions Privilégiées")
st.caption("Données simulées à des fins de démonstration (Faker + logique d'audit personnalisée)")

# st.tabs crée deux onglets cliquables ; tout ce qui est écrit dans un bloc
# "with tab_xxx:" ne s'affiche que quand cet onglet est sélectionné.
tab_ad, tab_wallix = st.tabs(["🔍 Audit Active Directory", "🛡️ Sessions Wallix à risque"])

# ==========================================================================
# ONGLET 1 : Audit Active Directory (code original, inchangé)
# ==========================================================================
with tab_ad:
    resultats = charger_donnees()

    # --- Indicateurs clés (KPI) en haut ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Comptes analysés", len(resultats))
    col2.metric("Risque critique", len(resultats[resultats["niveau_risque"] == "Critique"]))
    col3.metric("Risque élevé", len(resultats[resultats["niveau_risque"] == "Élevé"]))
    col4.metric("Score moyen", f"{resultats['score_risque'].mean():.1f}/10")

    st.divider()

    # --- Filtres dans la barre latérale ---
    st.sidebar.header("Filtres — Audit AD")

    departements = ["Tous"] + sorted(resultats["departement"].unique().tolist())
    dept_choisi = st.sidebar.selectbox("Département", departements)

    niveaux = ["Tous"] + sorted(resultats["niveau_risque"].unique().tolist())
    niveau_choisi = st.sidebar.selectbox("Niveau de risque", niveaux)

    score_min = st.sidebar.slider("Score minimum", 0.0, 10.0, 0.0, 0.5)

    # --- Application des filtres ---
    donnees_filtrees = resultats.copy()
    if dept_choisi != "Tous":
        donnees_filtrees = donnees_filtrees[donnees_filtrees["departement"] == dept_choisi]
    if niveau_choisi != "Tous":
        donnees_filtrees = donnees_filtrees[donnees_filtrees["niveau_risque"] == niveau_choisi]
    donnees_filtrees = donnees_filtrees[donnees_filtrees["score_risque"] >= score_min]

    # --- Graphique : distribution des niveaux de risque ---
    st.subheader("Répartition par niveau de risque")
    repartition = donnees_filtrees["niveau_risque"].value_counts()
    st.bar_chart(repartition)

    # --- Graphique : score moyen par département ---
    st.subheader("Score de risque moyen par département")
    score_par_dept = donnees_filtrees.groupby("departement")["score_risque"].mean().sort_values(ascending=False)
    st.bar_chart(score_par_dept)

    # --- Tableau détaillé ---
    st.subheader(f"Détail des comptes ({len(donnees_filtrees)} résultats)")
    st.dataframe(
        donnees_filtrees[["nom", "departement", "groupe_ad", "score_risque", "niveau_risque"]],
        width="stretch",
        hide_index=True,
    )

# ==========================================================================
# ONGLET 2 : Sessions Wallix à risque (nouveau module UEBA)
# ==========================================================================
with tab_wallix:
    # Toute la logique d'affichage (KPIs, filtres, tableau, histogramme)
    # vit dans core/wallix_dashboard.py ; on se contente de l'appeler ici.
    render_wallix_dashboard()