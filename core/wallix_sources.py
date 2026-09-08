# -*- coding: utf-8 -*-
"""
Simulation de sessions PAM Wallix + injection d'anomalies contrôlées.

Suit la même logique que sources.py (génération AD) : profils réalistes,
reproductibilité via seed, DataFrame en sortie.

Logique UEBA : chaque entité (utilisateur ou compte de service) a un profil
comportemental propre (assets habituels, heure de connexion typique).
Une anomalie casse VOLONTAIREMENT un seul axe de ce profil (heure, asset,
durée, ou commande sensible) pour rester interprétable en Phase 5 (évaluation).

Point d'entrée du module UEBA (voir aussi wallix_features.py, wallix_model.py,
wallix_evaluation.py, wallix_dashboard.py) : ce fichier ne dépend d'aucun
autre module de core/, il crée les données brutes que tout le reste du
module UEBA consomme. Appelé par scripts/phase9_wallix_main.py.

Remarque sur la numérotation : les commentaires "Phase 1/3/4/5" dans les
fichiers wallix_*.py désignent l'ordre INTERNE au module UEBA (génération ->
features -> modèle -> évaluation), pas les scripts scripts/phaseN_*.py
du projet global. Correspondance : Phase "génération" = phase9_wallix_main.py,
Phase 3 (features) = phase10, Phase 4 (modèle) = phase11, Phase 5
(évaluation) = phase12.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
# ------------------------------geolocalistaion ---------------------------------------- #

from .wallix_geo import COUNTRY_COORDS, COMMON_COUNTRIES, UNUSUAL_COUNTRIES

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- #
# Configuration (autonome pour l'instant — pourra être fusionnée avec
# core/config.py plus tard si tu veux tout centraliser au même endroit)
# ---------------------------------------------------------------------- #
@dataclass
class WallixSimConfig:
    random_seed: int = 1337
    n_baseline_sessions: int = 2000
    anomaly_rate: float = 0.04
    date_start: datetime = field(default_factory=lambda: datetime(2026, 1, 1))
    simulation_days: int = 180
    duration_mean_log: float = 3.0      # ≈ 20 min typique
    duration_sigma_log: float = 0.6
    sensitive_commands: tuple = (
        "rm -rf", "DROP TABLE", "shutdown -h now", "passwd root",
        "chmod 777", "TRUNCATE TABLE", "DELETE FROM users",
    )


# ---------------------------------------------------------------------- #
# Profils comportementaux par entité
# ---------------------------------------------------------------------- #
@dataclass
class EntityProfile:
    """Décrit le comportement "normal" d'un utilisateur/compte de service.
    hour_loc/hour_scale = moyenne/écart-type de son heure de connexion
    habituelle (loi normale) ; habitual_assets/asset_weights = les machines
    qu'il touche d'habitude et à quelle fréquence relative. C'est CE profil
    qui sert de référence pour juger si une session est "anormale" plus tard.
    """
    """(...) docstring inchangé (...)"""
    username: str
    role: str
    habitual_assets: List[str]
    asset_weights: List[float]
    hour_loc: float
    hour_scale: float
    protocol: str = "SSH"
    # Pays depuis lequel ce profil se connecte habituellement (Phase 15).
    # On reste simple : UN SEUL pays habituel par profil (pas une liste
    # pondérée comme pour les assets), suffisant pour détecter l'anomalie
    # "connexion depuis un pays inhabituel pour CET utilisateur".
    habitual_country: str = "Tunisia"

def default_profiles() -> Dict[str, EntityProfile]:
    # 4 profils fixes et volontairement différents (dev, DBA, admin réseau,
    # compte de service qui tourne la nuit) pour que les anomalies injectées
    # plus bas restent visuellement/statistiquement distinctes du profil normal.
    return {
        "jean_dev": EntityProfile(
            username="jean_dev", role="Developer",
            habitual_assets=["app-dev-01", "git-prod", "app-staging"],
            asset_weights=[0.70, 0.25, 0.05],
            hour_loc=10.0, hour_scale=1.8, protocol="SSH",
        ),
        "sara_dba": EntityProfile(
            username="sara_dba", role="DBA",
            habitual_assets=["prod-db-01", "backup-db", "prod-db-02"],
            asset_weights=[0.65, 0.25, 0.10],
            hour_loc=14.0, hour_scale=2.5, protocol="SSH",
        ),
        "marc_netadmin": EntityProfile(
            username="marc_netadmin", role="Network Admin",
            habitual_assets=["fw-edge-01", "fw-edge-02", "switch-core-01"],
            asset_weights=[0.45, 0.35, 0.20],
            hour_loc=9.0, hour_scale=2.0, protocol="HTTPS",
        ),
        "crypto_bot": EntityProfile(
            username="crypto_bot", role="Service Account",
            habitual_assets=["backup-db"],
            asset_weights=[1.0],
            hour_loc=2.0, hour_scale=0.4, protocol="SSH",
        ),
    }


def _all_assets(profiles: Dict[str, EntityProfile]) -> List[str]:
    seen = set()
    for p in profiles.values():
        seen.update(p.habitual_assets)
    return sorted(seen)


# ---------------------------------------------------------------------- #
# Générateur
# ---------------------------------------------------------------------- #
class WallixSessionGenerator:
    def __init__(self, profiles: Dict[str, EntityProfile], config: WallixSimConfig):
        self.profiles = profiles
        self.config = config
        self._all_assets = _all_assets(profiles)
        np.random.seed(self.config.random_seed)

    def generate_baseline(self, n_sessions: int) -> pd.DataFrame:
        rows: List[dict] = []
        usernames = list(self.profiles.keys())
        attempts = 0
        while len(rows) < n_sessions and attempts < n_sessions * 20:
            attempts += 1
            username = np.random.choice(usernames)
            profile = self.profiles[username]

            day_offset = np.random.randint(0, self.config.simulation_days)
            current_date = self.config.date_start + timedelta(days=int(day_offset))
            is_weekend = current_date.weekday() >= 5

            if is_weekend and profile.role != "Service Account":
                if np.random.rand() > 0.03:
                    continue

            rows.append(self._build_session_row(profile, current_date, anomaly_type="none"))

        df = pd.DataFrame(rows[:n_sessions])
        logger.info("Baseline générée : %d sessions", len(df))
        return df

    def inject_anomalies(self, n_anomalies: int) -> pd.DataFrame:
        rows: List[dict] = []
        usernames = list(self.profiles.keys())
        anomaly_types = ["unusual_hour", "unusual_asset", "unusual_duration", "sensitive_command", "unusual_country"]
        for _ in range(n_anomalies):
            username = np.random.choice(usernames)
            profile = self.profiles[username]
            anomaly_type = np.random.choice(anomaly_types)
            day_offset = np.random.randint(0, self.config.simulation_days)
            current_date = self.config.date_start + timedelta(days=int(day_offset))
            rows.append(self._build_session_row(profile, current_date, anomaly_type=anomaly_type))

        df = pd.DataFrame(rows)
        logger.info("Anomalies injectées : %d sessions", len(df))
        return df

    def _build_session_row(self, profile: EntityProfile, date, anomaly_type: str) -> dict:
        # Heure (donnée cyclique -> modulo, jamais clip)
        if anomaly_type == "unusual_hour":
            hour_raw = np.random.normal(loc=3.0, scale=1.5)
        else:
            hour_raw = np.random.normal(loc=profile.hour_loc, scale=profile.hour_scale)
        hour = int(round(hour_raw)) % 24
        minute = int(np.random.randint(0, 60))

        # Asset cible
        if anomaly_type == "unusual_asset":
            candidates = [a for a in self._all_assets if a not in profile.habitual_assets]
            asset = np.random.choice(candidates) if candidates else np.random.choice(self._all_assets)
        else:
            asset = np.random.choice(profile.habitual_assets, p=profile.asset_weights)
        if anomaly_type == "unusual_country":
            country = np.random.choice(UNUSUAL_COUNTRIES)
        else:
            country = profile.habitual_country
        country_lat, country_lon = COUNTRY_COORDS[country]

        # Durée (log-normale : toujours positive, asymétrique)
        base_duration = np.random.lognormal(
            mean=self.config.duration_mean_log, sigma=self.config.duration_sigma_log
        )
        if anomaly_type == "unusual_duration":
            duration_minutes = round(base_duration * np.random.uniform(6, 12), 1)
        else:
            duration_minutes = round(base_duration, 1)

        # Commandes / risque
        commands_count = max(1, int(np.random.poisson(lam=duration_minutes / 4)))
        if anomaly_type == "sensitive_command":
            triggered_command = np.random.choice(self.config.sensitive_commands)
            risk_flag = 1
        elif np.random.rand() < 0.01:
            triggered_command = np.random.choice(self.config.sensitive_commands)
            risk_flag = 1
        else:
            triggered_command = None
            risk_flag = 0

        timestamp = date.replace(hour=hour, minute=minute, second=int(np.random.randint(0, 60)))

        return {
            "session_id": None,
            "requestor_user": profile.username,
            "role": profile.role,
            "target_asset": asset,
            "country": country,
            "country_lat": country_lat,
            "country_lon": country_lon,
            "protocol": profile.protocol,
            "start_time": timestamp,
            "duration_minutes": duration_minutes,
            "hour": hour,
            "is_weekend": int(timestamp.weekday() >= 5),
            "commands_count": commands_count,
            "triggered_sensitive_command": triggered_command,
            "risk_flag": risk_flag,
            "is_anomaly": 0 if anomaly_type == "none" else 1,
            "anomaly_type": anomaly_type,
        }

    def generate(self) -> pd.DataFrame:
        """Point d'entrée public : combine baseline (comportement normal) et
        anomalies injectées en un seul DataFrame mélangé. C'est cette méthode
        qu'appelle scripts/phase9_wallix_main.py."""
        n_baseline = self.config.n_baseline_sessions
        n_anomalies = int(round(
            n_baseline * self.config.anomaly_rate / (1 - self.config.anomaly_rate)
        ))

        df_baseline = self.generate_baseline(n_baseline)
        df_anomalies = self.inject_anomalies(n_anomalies)

        df = pd.concat([df_baseline, df_anomalies], ignore_index=True)
        df = df.sample(frac=1, random_state=self.config.random_seed).reset_index(drop=True)
        df["session_id"] = [f"PAM-{i:05d}" for i in range(1, len(df) + 1)]
        df["start_time"] = pd.to_datetime(df["start_time"])
        df = df.sort_values("start_time").reset_index(drop=True)

        logger.info(
            "Dataset final : %d sessions (%d anomalies, %.1f%%)",
            len(df), df["is_anomaly"].sum(), 100 * df["is_anomaly"].mean()
        )
        return df