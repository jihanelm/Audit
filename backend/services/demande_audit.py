import json
import os
import shutil

from fastapi import UploadFile, HTTPException
from reportlab.lib import colors
from reportlab.lib.units import cm
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.demande_audit import Demande_Audit
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from log_config import setup_logger

from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

logger = setup_logger()

PDF_DIR = "fiches_demandes_audit"
STATIC_DIR = "pictures"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def save_uploaded_file(upload_file: UploadFile):
    print(f"Trying to save file: {upload_file.filename}")  # Debugging
    try:
        upload_folder = "fichiers_attaches_audit"
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, upload_file.filename)

        # Écriture du fichier sur le disque
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        print(f"Saved to: {file_path}")  # Debugging
        logger.info("Fichier '%s' sauvegardé avec succès à l'emplacement : %s", upload_file.filename, file_path)
        return file_path
    except Exception as e:
        logger.error("Échec de l'enregistrement du fichier '%s' : %s", upload_file.filename, str(e))
        return None

"""def generate_audit_pdf(demande_audit) -> str:
    pdf_path = os.path.join(PDF_DIR, f"fiche_demande_audit_{demande_audit.id}.pdf")
    try:
        page_num = 1
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 2 * cm
        ROUGE_GCAM = colors.HexColor("#d5191e")
        VERT_GCAM = colors.HexColor("#01803D")

        def check_page_space(y, decrement=100):
            if y < 50:
                new_page()
                c.setFont("Times-Roman", 12)
                return height - 2 * cm
            return y

        def draw_footer(page_num):
            c.setFont("Times-Italic", 10)  # Italic
            c.drawString(50, 20, "Interne")
            c.setFont("Times-Roman", 10)
            c.drawRightString(width - 50, 20, f"Page {page_num}")

        def new_page():
            nonlocal page_num
            draw_footer(page_num)
            c.showPage()
            page_num += 1
            c.setFont("Times-Roman", 12)
            draw_header()

        def draw_header():
            logo_width = 120
            logo_y = height - 80
            logo_height = 60

            # Texte en haut à gauche
            c.setFillColor(colors.gray)
            c.setFont("Times-Bold", 10)
            c.drawString(50, height - 40, "Groupe Crédit Agricole du Maroc")
            c.setFont("Times-Roman", 10)
            c.drawString(50, height - 55, "Direction Centrale Sécurité")
            c.drawString(50, height - 70, "Direction Sécurité de l'information")


            # Logo en haut à droite
            try:
                logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pictures", "logo.png"))
                c.drawImage(logo_path, width - 50 - logo_width, logo_y, width=logo_width, height=logo_height,
                            preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Erreur chargement logo: {e}")
                c.rect(width - 50 - logo_width, height - 50, logo_width, logo_height)

        def draw_modern_table(rows, x_start, y_start, col_widths, fill_color=colors.whitesmoke):
            y = y_start
            for index, row in enumerate(rows):
                # Calcul de la hauteur maximale en fonction du nombre de lignes
                line_count = max(len(str(cell).split('\n')) for cell in row)
                row_height = 14 * line_count + 6  # ligne + padding

                # Vérifie si assez de place, sinon page suivante
                if y - row_height < 50:
                    new_page()
                    y = height - 3 * cm

                # Fond alterné
                if index % 2 == 0:
                    c.setFillColor(fill_color)
                    c.rect(x_start, y - row_height, sum(col_widths), row_height, fill=1, stroke=0)

                # Texte
                c.setFillColor(colors.black)
                x = x_start
                for idx, cell in enumerate(row):
                    c.rect(x, y - row_height, col_widths[idx], row_height)  # encadrement
                    lines = str(cell).split('\n')
                    for i, line in enumerate(lines):
                        c.drawString(x + 4, y - 14 - (i * 12), line)
                    x += col_widths[idx]
                y -= row_height

            return y - 10

        draw_header()
        y -= 60
        c.setFont("Times-Bold", 18)
        c.setFillColor(ROUGE_GCAM)
        c.drawCentredString(width / 2, y, "Fiche de demande des audits sécurités")
        c.setFillColor(colors.black)
        y -= 30

        c.setFont("Times-Roman", 11)
        y = draw_modern_table([
            ["Date", demande_audit.date_creation],
            ["Nom de l'application cible", demande_audit.nom_app],
        ], 50, y, [150, 350])

        intro_text = (
            "Cette fiche mandate l’équipe sécurité d’information GCAM à réaliser les audits de sécurité visant à évaluer le niveau de sécurité de l’application cible. "
            "Le chef de projet (CP) doit remplir et faire parvenir le document par courriel au responsable sécurité /équipe sécurité d’information pour validation et le lancement des différents audits."
        )

        # Définir un style justifié
        style_sheet = getSampleStyleSheet()
        justified_style = ParagraphStyle(
            'Justified',
            parent=style_sheet['Normal'],
            fontName='Times-Roman',
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY
        )

        # Créer le paragraphe
        paragraph = Paragraph(intro_text, justified_style)

        # Cadre pour contenir le texte justifié
        frame_height = 80  # ajuste selon la place
        frame = Frame(50, y - frame_height, width - 100, frame_height, showBoundary=0)
        frame.addFromList([paragraph], c)

        y -= frame_height + 10


        c.setFont("Times-Bold", 14)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Identification du demandeur")
        c.setFillColor(colors.black)
        y -= 20

        c.setFont("Times-Roman", 11)
        y = draw_modern_table([
            ["Nom et prénom (CP)", f"{demande_audit.demandeur_nom_1} {demande_audit.demandeur_prenom_1}"],
            ["Entité", demande_audit.demandeur_entite_1],
            ["Courrier électronique", demande_audit.demandeur_email_1],
            ["Téléphone", demande_audit.demandeur_phone_1],
            ["Nom et prénom (Backup)", f"{demande_audit.demandeur_nom_2} {demande_audit.demandeur_prenom_2}"],
            ["Entité", demande_audit.demandeur_entite_2],
            ["Courrier électronique", demande_audit.demandeur_email_2],
            ["Téléphone", demande_audit.demandeur_phone_2]
        ], 50, y, [200, 300])

        y -= 20

        c.setFont("Times-Bold", 14)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Application ou Solution à tester")
        c.setFillColor(colors.black)
        y -= 20

        c.setFont("Times-Roman", 11)
        y = draw_modern_table([
            ["Nom", demande_audit.nom_app],
            ["Description", demande_audit.description],
            ["Fonctionnalités concernées", demande_audit.liste_fonctionalites]
        ], 50, y, [200, 300])

        y -= 10

        c.setFont("Times-Bold", 12)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Type d'application")
        y -= 20

        c.setFont("Times-Roman", 11)

        app_types = ["Web", "Mobile", "Client Lourd"]
        selected_types = demande_audit.type_app or ''
        type_rows = []
        for t in app_types:
            check = "✔" if t in selected_types else "☐"
            type_rows.append([f"{check} {t}"])

        y = draw_modern_table(type_rows, 50, y, [width - 100])

        y -= 20

        app_types_2 = ["Externe", "Interne"]
        selected_types_2 = demande_audit.type_app_2 or ''
        type_rows_2 = []
        for t in app_types_2:
            check = "✔" if t in selected_types_2 else "☐"
            type_rows_2.append([f"{check} {t}"])

        y = draw_modern_table(type_rows_2, 50, y, [width - 100])

        y -= 20

        c.setFont("Times-Bold", 14)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Exigences techniques")
        c.setFillColor(colors.black)
        y -= 20

        c.setFont("Times-Roman", 11)
        exigence_fields = [
            ("Architecture projet", str(demande_audit.architecture_projet)),
            ("Protection WAF", str(demande_audit.protection_waf)),
            ("Commentaires WAF", demande_audit.commentaires_waf),
            ("Ports ouverts", str(demande_audit.ports)),
            ("Liste des ports", demande_audit.liste_ports),
            ("Certificat SSL", str(demande_audit.cert_ssl_domain_name)),
            ("Commentaires SSL", demande_audit.commentaires_cert_ssl_domain_name),
        ]
        y = draw_modern_table(exigence_fields, 50, y, [200, 300])

        y -= 20

        c.setFont("Times-Bold", 14)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Prérequis techniques")
        c.setFillColor(colors.black)
        y -= 20

        c.setFont("Times-Roman", 11)

        prereq_fields = [
            ("Système d'exploitation", demande_audit.sys_exploitation),
            ("Logiciels installés", demande_audit.logiciels_installes),
            ("Environnement de tests", demande_audit.env_tests),
            ("Données de prod", str(demande_audit.donnees_prod)),
            ("SI actifs", demande_audit.liste_si_actifs),
            ("Compte admin", demande_audit.compte_admin),
            ("Nom de domaine", demande_audit.nom_domaine),
            ("URL", demande_audit.url_app),
            ("Profil test", demande_audit.compte_test_profile),
            ("Urgence", demande_audit.urgence)
        ]

        y = draw_modern_table(prereq_fields, 50, y, [200, 300])

        y -= 10

        # --- Pièces jointes ---
        c.setFont("Times-Bold", 11)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Pièces jointes")
        c.setFillColor(colors.black)
        y -= 10

        c.setFont("Times-Roman", 10)

        if demande_audit.fichiers_attaches:
            if isinstance(demande_audit.fichiers_attaches, str):
                try:
                    fichiers_list = json.loads(demande_audit.fichiers_attaches)
                except json.JSONDecodeError:
                    fichiers_list = [demande_audit.fichiers_attaches]
            else:
                fichiers_list = demande_audit.fichiers_attaches
        else:
            fichiers_list = []

        if not fichiers_list:
            fichiers_list = ["Aucun"]

        # Ligne de titre unique
        fichier_rows = [("Fichier attaché", "")] + [("", f) for f in fichiers_list]

        # Affichage
        y = draw_modern_table(fichier_rows, 50, y, [200, 300])

        y -= 40

        c.setFont("Times-BoldItalic", 10)
        c.setFillColor(ROUGE_GCAM)
        c.drawCentredString(width / 2, y, "_Fin de document_")
        c.setFillColor(colors.black)

        draw_footer(page_num)
        c.save()
        return pdf_path

    except Exception as e:
        print(f"Erreur lors de la génération de la fiche: {e}")
        return """""

def generate_audit_pdf(demande_audit) -> str:
    pdf_path = os.path.join(PDF_DIR, f"fiche_demande_audit_{demande_audit.id}.pdf")

    # Load the HTML template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('fiche_demande_audit_template.html')

    try:
        template = env.get_template("fiche_demande_audit_template.html")

        # Prepare data
        fichiers_list = []
        if demande_audit.fichiers_attaches:
            if isinstance(demande_audit.fichiers_attaches, str):
                try:
                    fichiers_list = json.loads(demande_audit.fichiers_attaches)
                except json.JSONDecodeError:
                    fichiers_list = [demande_audit.fichiers_attaches]
            else:
                fichiers_list = demande_audit.fichiers_attaches
        if not fichiers_list:
            fichiers_list = ["Aucun"]

        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pictures", "logo.png"))
        logo_path_url = f"file:///{logo_path.replace(os.sep, '/')}"

        html_content = template.render(demande_audit=demande_audit, fichiers=fichiers_list, logo_path=logo_path_url)

        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path

    except Exception as e:
        print(f"Erreur lors de la génération: {e}")
        return ""

def create_demande_audit(
        type_audit=str,
        demandeur_nom_1=str,
        demandeur_prenom_1=str,
        demandeur_email_1=str,
        demandeur_phone_1=str,
        demandeur_entite_1=str,
        demandeur_nom_2=str,
        demandeur_prenom_2=str,
        demandeur_email_2=str,
        demandeur_phone_2=str,
        demandeur_entite_2=str,
        nom_app=str,
        description=str,
        liste_fonctionalites=str,
        type_app=str,
        type_app_2= str,
        architecture_projet=bool,
        commentaires_archi=str,
        protection_waf=bool,
        commentaires_waf=str,
        ports=bool,
        liste_ports=str,
        cert_ssl_domain_name=bool,
        commentaires_cert_ssl_domain_name=str,
        sys_exploitation=str,
        logiciels_installes=str,
        env_tests=str,
        donnees_prod=bool,
        liste_si_actifs=str,
        compte_admin=str,
        nom_domaine=str,
        url_app=str,
        compte_test_profile=str,
        urgence=str,
        fichiers_attaches=Optional[UploadFile],
        db= Session
) -> Demande_Audit:
    logger.info("Début de la création d'un audit.")
    logger.debug("Création d'un audit par %s %s (%s)", demandeur_prenom_1, demandeur_nom_1,
                 demandeur_email_1)

    fichiers_paths = []
    for file in fichiers_attaches:
        path = save_uploaded_file(file)
        if path:
            fichiers_paths.append(path)
        else:
            raise HTTPException(status_code=400, detail=f"Failed to upload file: {file.filename}")

    # Création de l'objet ORM
    demande = Demande_Audit(
        type_audit=type_audit,
        demandeur_nom_1=demandeur_nom_1,
        demandeur_prenom_1=demandeur_prenom_1,
        demandeur_email_1=demandeur_email_1,
        demandeur_phone_1=demandeur_phone_1,
        demandeur_entite_1=demandeur_entite_1,
        demandeur_nom_2=demandeur_nom_2,
        demandeur_prenom_2=demandeur_prenom_2,
        demandeur_email_2=demandeur_email_2,
        demandeur_phone_2=demandeur_phone_2,
        demandeur_entite_2=demandeur_entite_2,
        nom_app=nom_app,
        description=description,
        liste_fonctionalites=liste_fonctionalites,
        type_app=type_app,
        type_app_2=type_app_2,
        architecture_projet=architecture_projet,
        commentaires_archi=commentaires_archi,
        protection_waf=protection_waf,
        commentaires_waf=commentaires_waf,
        ports=ports,
        liste_ports=liste_ports,
        cert_ssl_domain_name=cert_ssl_domain_name,
        commentaires_cert_ssl_domain_name=commentaires_cert_ssl_domain_name,
        sys_exploitation=sys_exploitation,
        logiciels_installes=logiciels_installes,
        env_tests=env_tests,
        donnees_prod=donnees_prod,
        liste_si_actifs=liste_si_actifs,
        compte_admin=compte_admin,
        nom_domaine=nom_domaine,
        url_app=url_app,
        compte_test_profile=compte_test_profile,
        urgence=urgence,
        fichiers_attaches=fichiers_paths
    )

    db.add(demande)
    db.commit()
    db.refresh(demande)

    logger.info("Audit inséré en base avec l'ID : %d", demande.id)

    # Génération du PDF
    pdf_path = generate_audit_pdf(demande)
    demande.fiche_demande_path = pdf_path
    db.commit()

    logger.info("Création de l'audit terminée avec succès. PDF généré : %s", pdf_path)

    return demande

def get_all_audits(db: Session) -> List[Demande_Audit]:
    demande_audits = db.query(Demande_Audit).all()
    logger.info("Récupération de tous les audits. Total : %d", len(demande_audits))
    return demande_audits


def get_audit_by_id(demande_audit_id: int, db: Session) -> Optional[Demande_Audit]:
    demande_audit = db.query(Demande_Audit).filter(Demande_Audit.id == demande_audit_id).first()
    if demande_audit:
        logger.info("Audit trouvé pour l'ID %d", demande_audit_id)
    else:
        logger.warning("Aucun audit trouvé pour l'ID %d", demande_audit_id)
    return demande_audit