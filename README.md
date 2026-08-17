# 🔒 Python AD Audit — Simulateur d'audit Active Directory

![Tests](https://github.com/RSassi22/python-ad-audit/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Projet personnel développé pendant un stage sécurité/infrastructure en environnement
bancaire (Active Directory, MECM, Qualys, bastion Wallix). Sans accès aux données réelles,
ce projet simule un environnement AD complet et applique une logique d'audit de sécurité
réaliste : détection de comptes inactifs, incohérences de droits, et corrélation avec des
vulnérabilités simulées façon Qualys — pour repérer les comptes cumulant privilèges élevés
et exposition critique.

## 📸 Aperçu

### Dashboard interactif
![Dashboard](docs/screenshots/dashboard.png)

### Rapport PDF automatique
![Rapport PDF](docs/screenshots/rapport_pdf.png)

## 🎯 Fonctionnalités

- **Génération de données AD fictives** réalistes (200 utilisateurs, départements, groupes AD, historique de connexion) via Faker
- **Simulation de scan de vulnérabilités** façon Qualys (CVE, sévérité, statut de patch)
- **Moteur d'audit** détectant :
  - Comptes inactifs depuis plus de 90 jours
  - Incohérences département/groupe AD
  - Comptes à privilèges élevés sur des machines vulnérables non patchées
- **Score de risque combiné** (0-10) par utilisateur, pondéré et normalisé
- **Rapport PDF automatique** avec résumé exécutif et top 10 des risques
- **Dashboard interactif Streamlit** avec filtres en temps réel
- **Conteneurisé avec Docker** pour un déploiement en une commande
- **Tests unitaires + CI/CD** via GitHub Actions

## 🏗️ Architecture

\`\`\`
python-ad-audit/
├── core/                   # Package métier
│   ├── config.py           # Paramètres centralisés (dataclass)
│   ├── sources.py          # Génération des données AD et Qualys
│   ├── audit.py            # Règles de détection
│   ├── scoring.py          # Calcul du score de risque combiné
│   └── report.py           # Génération du rapport PDF
├── scripts/                # Scripts d'orchestration par phase
├── tests/                  # Tests unitaires (pytest)
├── dashboard.py            # Application Streamlit
├── Dockerfile
└── .github/workflows/      # CI GitHub Actions
\`\`\`

## 🚀 Installation

### Option 1 — Environnement local

\`\`\`bash
git clone https://github.com/TON_USERNAME/python-ad-audit.git
cd python-ad-audit
pip install -r requirements.txt
\`\`\`

### Option 2 — Docker

\`\`\`bash
docker build -t audit-ad-dashboard .
docker run -p 8501:8501 audit-ad-dashboard
\`\`\`

## ▶️ Utilisation

**Lancer le dashboard interactif :**
\`\`\`bash
streamlit run dashboard.py
\`\`\`
Puis ouvrir [http://localhost:8501](http://localhost:8501)

**Générer le rapport PDF :**
\`\`\`bash
python scripts/phase8_main.py
\`\`\`

**Lancer les tests :**
\`\`\`bash
pytest tests/ -v
\`\`\`

## 🧠 Logique de scoring

Chaque compte reçoit un score pondéré selon plusieurs facteurs de risque
(inactivité, incohérence de droits, appartenance à un groupe sensible,
sévérité des vulnérabilités associées, absence de patch), normalisé sur 10.

| Niveau | Score |
|---|---|
| Faible | 0 - 2 |
| Moyen | 2 - 5 |
| Élevé | 5 - 8 |
| Critique | 8 - 10 |

## 🛠️ Stack technique

Python · Pandas · Faker · Streamlit · ReportLab · Matplotlib · Docker · pytest · GitHub Actions

## 📌 Contexte

Projet réalisé dans le cadre d'un stage en sécurité/infrastructure bancaire, en l'absence
d'accès aux données de production. Toutes les données sont **entièrement fictives**,
générées par Faker.