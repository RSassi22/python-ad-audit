# -*- coding: utf-8 -*-
"""
core/wallix_geo.py

Données géographiques utilisées pour simuler le pays d'origine des
sessions Wallix (Phase 15). Fichier séparé pour ne pas alourdir
wallix_sources.py avec des données statiques.

Pas de vraie géolocalisation d'IP ici (pas de MaxMind/GeoIP2) : on simule
directement un pays par session, avec des coordonnées lat/long FIXES par
pays, suffisantes pour un affichage sur carte (st.map() dans le dashboard).
C'est un choix assumé pour un POC : pas besoin de précision ville par ville,
juste de distinguer "pays habituel" vs "pays inhabituel".
"""

# Coordonnées approximatives (capitale ou centre du pays), utilisées
# uniquement pour placer un point sur la carte du dashboard.
COUNTRY_COORDS = {
    "Tunisia":        (36.8065, 10.1815),
    "France":         (48.8566, 2.3522),
    "Morocco":        (33.9716, -6.8498),
    "Russia":         (55.7558, 37.6173),
    "Brazil":         (-15.7939, -47.8828),
    "Nigeria":        (9.0765, 7.3986),
    "North Korea":    (39.0392, 125.7625),
    "China":          (39.9042, 116.4074),
    "Vietnam":        (21.0278, 105.8342),
    "Ukraine":        (50.4501, 30.5234),
}

# Pays "habituels" pour la banque (là où on s'attend légitimement à voir
# des connexions). Le reste de COUNTRY_COORDS sert de réservoir de pays
# inhabituels pour les anomalies unusual_country.
COMMON_COUNTRIES = ["Tunisia", "France", "Morocco"]

UNUSUAL_COUNTRIES = [
    c for c in COUNTRY_COORDS if c not in COMMON_COUNTRIES
]