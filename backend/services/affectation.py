import os

from reportlab.lib import colors
from reportlab.lib.units import cm
from sqlalchemy.orm import Session, joinedload
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend.models.affectation import Affectation
from backend.models.auditeur import (Auditeur)
from backend.models.ip import IP
from backend.models.ports import Port
from backend.models.prestataire import Prestataire
from backend.schemas.affectation import AffectSchema
from backend.schemas.auditeur import AuditeurSchema
from backend.schemas.prestataire import PrestataireSchema

from log_config import setup_logger

logger = setup_logger()

def generate_affect_pdf(affect):
    logger.info(f"Génération du PDF pour l'affectation ID={affect.id}")
    pdf_dir = "fichiers_affectations"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"affect_{affect.id}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    try:
        page_num = 1
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 2 * cm

        ROUGE_GCAM = colors.HexColor("#d5191e")
        VERT_GCAM = colors.HexColor("#01803D")

        def draw_header():
            c.setFillColor(colors.gray)
            c.setFont("Times-Bold", 10)
            c.drawString(50, height - 40, "Groupe Crédit Agricole du Maroc")
            c.setFont("Times-Roman", 10)
            c.drawString(50, height - 55, "Direction Centrale Sécurité")
            c.drawString(50, height - 70, "Direction Sécurité de l'information")

            # Logo
            logo_width, logo_height = 120, 60
            logo_y = height - 80
            try:
                logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pictures", "logo.png"))
                c.drawImage(logo_path, width - 50 - logo_width, logo_y, width=logo_width, height=logo_height,
                            preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.warning(f"Erreur chargement logo: {e}")
                c.rect(width - 50 - logo_width, height - 50, logo_width, logo_height)

        def draw_footer(page_num):
            c.setFont("Times-Italic", 10)
            c.drawString(50, 20, "Interne")
            c.setFont("Times-Roman", 10)
            c.drawRightString(width - 50, 20, f"Page {page_num}")

        def new_page():
            nonlocal y, page_num
            draw_footer(page_num)
            c.showPage()
            page_num += 1
            c.setFont("Times-Roman", 12)
            draw_header()
            y = height - 2 * cm

        def check_space(decrement=100):
            nonlocal y
            if y - decrement < 50:
                new_page()
            y -= decrement

        def draw_modern_table(rows, x_start, y_start, col_widths, fill_color=colors.whitesmoke):
            nonlocal y
            y = y_start
            for index, row in enumerate(rows):
                line_count = max(len(str(cell).split('\n')) for cell in row)
                row_height = 14 * line_count + 6

                if y - row_height < 50:
                    new_page()
                    y = height - 2 * cm

                if index % 2 == 0:
                    c.setFillColor(fill_color)
                    c.rect(x_start, y - row_height, sum(col_widths), row_height, fill=1, stroke=0)

                c.setFillColor(colors.black)
                x = x_start
                for idx, cell in enumerate(row):
                    c.rect(x, y - row_height, col_widths[idx], row_height)
                    lines = str(cell).split('\n')
                    for i, line in enumerate(lines):
                        c.drawString(x + 4, y - 14 - (i * 12), line)
                    x += col_widths[idx]
                y -= row_height

            return y - 10

        draw_header()

        # Titre
        c.setFont("Times-Bold", 16)
        c.setFillColor(ROUGE_GCAM)
        c.drawCentredString(width / 2, height - 100, "Fiche d'Affectation d'Audit")
        y = height - 100

        check_space(30)
        c.setFont("Times-Bold", 14)
        c.setFillColor(VERT_GCAM)
        c.drawString(50, y, "Informations Générales:")
        y -= 20

        c.setFont("Times-Roman", 11)
        c.setFillColor(colors.black)

        general_info = [
            ["ID Audit", affect.demande_audit_id],
            ["Nom de l'Application", affect.demande_audit.nom_app],
            ["Type d'audit", affect.type_audit],
            ["Prestataire", affect.prestataire.nom],
            ["Date d'affectation", affect.date_affectation.strftime('%d/%m/%Y')],
        ]
        y = draw_modern_table(general_info, 50, y, [150, 350])

        # Infos Demandeur
        if hasattr(affect, 'demande_audit') and affect.demande_audit:
            check_space(30)
            c.setFont("Times-Bold", 14)
            c.setFillColor(VERT_GCAM)
            c.drawString(50, y, "Informations du Demandeur:")
            y -= 20

            c.setFont("Times-Roman", 11)
            c.setFillColor(colors.black)

            demandeur_info = [
                ["Champ", "Valeur"],
                ["Nom", affect.demande_audit.demandeur_nom_1],
                ["Prénom", affect.demande_audit.demandeur_prenom_1],
                ["Email", affect.demande_audit.demandeur_email_1],
                ["Téléphone", affect.demande_audit.demandeur_phone_1],
                ["Entité", affect.demande_audit.demandeur_entite_1],
            ]
            y = draw_modern_table(demandeur_info, 50, y, [150, 350])

        # Auditeurs
        if hasattr(affect, 'auditeurs') and affect.auditeurs:
            check_space(30)
            c.setFont("Times-Bold", 14)
            c.setFillColor(VERT_GCAM)
            c.drawString(50, y, "Liste des Auditeurs:")
            y -= 20

            c.setFont("Times-Roman", 11)
            c.setFillColor(colors.black)

            auditeur_rows = [["Nom", "Prénom", "Email", "Téléphone"]]
            for a in affect.auditeurs:
                auditeur_rows.append([a.nom, a.prenom, a.email, a.phone])

            y = draw_modern_table(auditeur_rows, x_start=50, y_start=y, col_widths=[100, 100, 200, 100])

        # IPs + Ports
        if hasattr(affect, 'ips') and affect.ips:
            check_space(30)
            c.setFont("Times-Bold", 14)
            c.setFillColor(VERT_GCAM)
            c.drawString(50, y, "IPs affectées:")
            y -= 20

            c.setFont("Times-Roman", 11)
            c.setFillColor(colors.black)

            ip_rows = [["Adresse IP", "Port", "Statut"]]
            for ip in affect.ips:
                for port in ip.ports:
                    ip_rows.append([ip.adresse_ip, port.port, port.status])

            y = draw_modern_table(ip_rows, x_start=50, y_start=y, col_widths=[200, 100, 100])

        draw_footer(page_num)
        c.save()

        logger.debug(f"PDF généré avec succès : {pdf_path}")
        logger.info("PDF généré avec succès.")
        return pdf_path.replace("\\", "/")

    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF : {e}", exc_info=True)
        raise
def create_affect(db: Session, affect_data: AffectSchema):
    logger.info("Création d'une nouvelle affectation d'audit")
    affect = Affectation(
        type_audit=affect_data.type_audit,
        demande_audit_id=affect_data.demande_audit_id,
        prestataire_id=affect_data.prestataire_id
    )
    db.add(affect)
    db.commit()
    db.refresh(affect)

    for auditeur_data in affect_data.auditeurs:
        existing_auditeur = db.query(Auditeur).filter(
            Auditeur.email == auditeur_data.email
        ).first()

        if not existing_auditeur:
            logger.debug(f"Création du nouvel auditeur : {auditeur_data.email}")
            auditeur = Auditeur(
                nom=auditeur_data.nom,
                prenom=auditeur_data.prenom,
                email=auditeur_data.email,
                phone=auditeur_data.phone,
                prestataire_id=auditeur_data.prestataire_id
            )
            db.add(auditeur)
            db.commit()
            db.refresh(auditeur)
            affect.auditeurs.append(auditeur)
        else:
            logger.debug(f"Auditeur déjà existant trouvé : {existing_auditeur.email}")
            affect.auditeurs.append(existing_auditeur)

    for ip_data in affect_data.ips:
        existing_ip = db.query(IP).filter(
            IP.adresse_ip == ip_data.adresse_ip
        ).first()

        if not existing_ip:
            logger.debug(f"Ajout d'une nouvelle IP : {ip_data.adresse_ip}")
            ip = IP(
                adresse_ip=ip_data.adresse_ip,
                affectation_id=affect.id
            )
            db.add(ip)
            db.commit()
            db.refresh(ip)

            # Ajouter les ports
            for port_data in ip_data.ports:
                logger.debug(f"Ajout du port {port_data.port}/{port_data.status} à l'IP {ip.adresse_ip}")
                port = Port(
                    port=port_data.port,
                    status=port_data.status,
                    ip_id=ip.id
                )
                db.add(port)
            db.commit()
            affect.ips.append(ip)
        else:
            logger.warning(f"IP déjà existante détectée : {existing_ip.adresse_ip}")
            affect.ips.append(existing_ip)

    affectationpath = generate_affect_pdf(affect)
    affect.affectationpath = affectationpath
    db.commit()

    logger.info(f"Affectation créée avec succès : ID={affect.id}")
    return affect

def get_affect(db: Session, affectation_id: int):
    logger.info(f"Recherche de l'affectation avec ID: {affectation_id}")
    affect = db.query(Affectation)\
        .options(
            joinedload(Affectation.auditeurs),
            joinedload(Affectation.ips).joinedload(IP.ports),
            joinedload(Affectation.prestataire),
            joinedload(Affectation.audit)
        )\
        .filter(Affectation.id == affectation_id)\
        .first()
    if affect:
        logger.info(f"Affectation trouvée: {affect.id}")
    else:
        logger.warning(f"Aucune affectation trouvée avec ID: {affectation_id}")
    return affect

def list_affects(db: Session):
    logger.info("Récupération de toutes les affectations")
    affects = db.query(Affectation).all()
    logger.info(f"{len(affects)} affectation(s) récupérée(s)")
    return affects

def create_auditeur(db: Session, auditeur_data: AuditeurSchema):
    auditeur = Auditeur(
        nom=auditeur_data.nom,
        prenom=auditeur_data.prenom,
        email=auditeur_data.email,
        phone=auditeur_data.phone,
        prestataire_id=auditeur_data.prestataire_id
    )
    db.add(auditeur)
    db.commit()
    db.refresh(auditeur)
    return auditeur

def create_prestataire(db: Session, prestataire_data: PrestataireSchema):
    prestataire = Prestataire(
        nom=prestataire_data.nom
    )
    db.add(prestataire)
    db.commit()
    db.refresh(prestataire)
    return prestataire

def list_auditeurs(db: Session):
    return db.query(Auditeur).all()

def list_ips(db: Session):
    return db.query(IP).all()

def delete_auditeur(db: Session, auditeur_id: int):
    logger.info(f"Tentative de suppression de l'auditeur ID {auditeur_id}")
    auditeur = db.query(Auditeur).filter(Auditeur.id == auditeur_id).first()
    if not auditeur:
        logger.warning(f"Auditeur ID {auditeur_id} non trouvé")
        return None

    for affect in auditeur.affects:
        affect.auditeurs.remove(auditeur)

    db.delete(auditeur)
    db.commit()
    logger.info(f"Auditeur ID {auditeur_id} supprimé")
    return auditeur

def update_auditeur(db: Session, auditeur_id: int, auditeur_data: AuditeurSchema):
    logger.info(f"Mise à jour de l'auditeur ID {auditeur_id}")
    auditeur = db.query(Auditeur).filter(Auditeur.id == auditeur_id).first()
    if not auditeur:
        logger.warning(f"Auditeur ID {auditeur_id} non trouvé pour mise à jour")
        return None

    auditeur.nom = auditeur_data.nom
    auditeur.prenom = auditeur_data.prenom
    auditeur.email = auditeur_data.email
    auditeur.phone = auditeur_data.phone
    auditeur.prestataire_id = auditeur_data.prestataire_id

    db.commit()
    db.refresh(auditeur)
    logger.debug(f"Auditeur ID {auditeur_id} mis à jour")
    logger.info("Auditeur mis a jour avec succes")
    return auditeur
