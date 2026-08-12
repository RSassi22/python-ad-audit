import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .config import Config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Génère un rapport d'audit AD au format PDF, à partir des scores de risque."""

    def __init__(self, config: Config):
        self.config = config
        self.styles = getSampleStyleSheet()

    def generer(self, resultats: pd.DataFrame, chemin_sortie: str = "outputs/rapport_audit.pdf") -> None:
        chemin = Path(chemin_sortie)
        chemin.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(chemin), pagesize=A4,
                                 topMargin=2*cm, bottomMargin=2*cm)
        elements = []

        elements += self._section_titre()
        elements += self._section_resume(resultats)
        elements += self._section_top_risques(resultats)

        doc.build(elements)
        logger.info(f"Rapport PDF généré : {chemin}")

    def _section_titre(self) -> list:
        titre_style = ParagraphStyle(
            "TitrePrincipal", parent=self.styles["Title"], fontSize=20, spaceAfter=6
        )
        sous_titre_style = ParagraphStyle(
            "SousTitre", parent=self.styles["Normal"], fontSize=10, textColor=colors.grey
        )
        date_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")

        return [
            Paragraph("Rapport d'audit Active Directory", titre_style),
            Paragraph(f"Généré automatiquement le {date_generation}", sous_titre_style),
            Spacer(1, 1*cm),
        ]

    def _section_resume(self, resultats: pd.DataFrame) -> list:
        nb_total = len(resultats)
        nb_critiques = len(resultats[resultats["niveau_risque"] == "Critique"])
        nb_eleves = len(resultats[resultats["niveau_risque"] == "Élevé"])
        score_moyen = round(resultats["score_risque"].mean(), 1)

        texte = (
            f"Sur <b>{nb_total}</b> comptes analysés : "
            f"<b>{nb_critiques}</b> présentent un risque critique, "
            f"<b>{nb_eleves}</b> un risque élevé. "
            f"Score de risque moyen : <b>{score_moyen}/10</b>."
        )

        return [
            Paragraph("Résumé exécutif", self.styles["Heading2"]),
            Paragraph(texte, self.styles["Normal"]),
            Spacer(1, 1*cm),
        ]

    def _section_top_risques(self, resultats: pd.DataFrame) -> list:
        top = resultats.head(10)

        donnees_tableau = [["Nom", "Département", "Groupe AD", "Score", "Niveau"]]
        for _, ligne in top.iterrows():
            donnees_tableau.append([
                ligne["nom"], ligne["departement"], ligne["groupe_ad"],
                str(ligne["score_risque"]), ligne["niveau_risque"]
            ])

        tableau = Table(donnees_tableau, colWidths=[4*cm, 3*cm, 4*cm, 2*cm, 2.5*cm])
        tableau.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ]))

        return [
            Paragraph("Top 10 des comptes à risque", self.styles["Heading2"]),
            tableau,
        ]