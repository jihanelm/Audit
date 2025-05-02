from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.affectation import Affectation
from backend.models.audit import Audit
from backend.models.auditeur import Auditeur
from backend.models.demande_audit import Demande_Audit
from backend.models.ip import IP
from backend.models.ports import Port
from backend.schemas.audit import AuditBase, AuditResponse
from typing import List
from log_config import setup_logger

logger = setup_logger()

def create_audit(db: Session, audit_data: AuditBase):
    logger.info("Création d'une nouvelle affectation d'audit")

    auditeurs = db.query(Auditeur).filter(Auditeur.id.in_(audit_data.auditeur_ids)).all()

    audit = Audit(
        demande_audit_id=audit_data.demande_audit_id,
        prestataire_id=audit_data.prestataire_id,
        affectation_id=audit_data.affectation_id,
        auditeurs=auditeurs
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    logger.info(f"Affectation créée avec succès : ID={audit.id}")
    return audit

def get_audit(db: Session, audit_id: int):
    logger.info(f"Recherche de l'affectation avec ID: {audit_id}")
    audit = db.query(Audit)\
        .options(
            joinedload(Audit.prestataire),
            joinedload(Audit.demande_audit),
            joinedload(Audit.affectation),
            joinedload(Audit.auditeurs)
        )\
        .filter(Audit.id == audit_id)\
        .first()
    if audit:
        logger.info(f"Affectation trouvée: {audit.id}")
    else:
        logger.warning(f"Aucune affectation trouvée avec ID: {audit_id}")
    return audit

def list_audits(db: Session):
    logger.info("Récupération de touts les audits avec relations")
    audits = db.query(Audit)\
        .options(
            joinedload(Audit.prestataire),
            joinedload(Audit.demande_audit),
            joinedload(Audit.affectation).joinedload(Affectation.auditeurs)
        )\
        .all()
    logger.info(f"{len(audits)} audit(s) récupéré(s)")
    return audits

def update_audit_duration(audit: Audit):
    now = datetime.utcnow()

    if audit.etat == "En cours":
        if audit.start_time:
            elapsed_seconds = (now - audit.start_time).total_seconds()
            elapsed_days = elapsed_seconds / 86400  # Convertir secondes -> jours
            audit.total_duration += elapsed_days
            audit.start_time = now
    elif audit.etat in ["Suspendu", "Terminé"]:
        if audit.start_time:
            elapsed_seconds = (now - audit.start_time).total_seconds()
            elapsed_days = elapsed_seconds / 86400
            audit.total_duration += elapsed_days
            audit.start_time = None
            audit.last_pause_time = now

def change_audit_etat(db: Session, audit_id: int, new_etat: str):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")

    update_audit_duration(audit)

    audit.etat = new_etat
    db.commit()
    db.refresh(audit)
    return audit
