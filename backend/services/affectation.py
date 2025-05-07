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

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from log_config import setup_logger

logger = setup_logger()

def generate_affect_pdf(affect):
    logger.info(f"Génération du PDF via HTML pour l'affectation ID={affect.id}")

    # Load the HTML template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('affect_template.html')

    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pictures", "logo.png"))
    logo_path_url = f"file:///{logo_path.replace(os.sep, '/')}"

    # Render the HTML with the data
    html_content = template.render(affect=affect, logo_path=logo_path_url)

    # Prepare output folder
    pdf_dir = "fichiers_affectations"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"fiche_affectation_{affect.id}_{affect.demande_audit.nom_app}_{affect.prestataire.nom}_{affect.date_affectation}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    # Generate PDF from HTML
    HTML(string=html_content).write_pdf(pdf_path)

    logger.info("PDF généré avec succès via HTML.")
    return pdf_path.replace("\\", "/")

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
            joinedload(Affectation.demande_audit)
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
