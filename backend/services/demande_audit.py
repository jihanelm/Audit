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

def generate_audit_pdf(demande_audit) -> str:
    pdf_path = os.path.join(PDF_DIR, f"fiche_demande_audit_{demande_audit.id}_{demande_audit.nom_app}_{demande_audit.date_creation}.pdf")

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