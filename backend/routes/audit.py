from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.schemas.audit import AuditResponse, AuditBase
from backend.services.audit import create_audit, get_audit, list_audits
from database import get_db
from typing import List

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/audits/", response_model=AuditResponse, summary="Creer un audit", description="Permet de creer un audit")
def create_audit_route(audit_data: AuditBase, db: Session = Depends(get_db)):
    logger.debug(f"Création d'un audit pour demande_audit_id {audit_data.demande_audit_id}")
    logger.info(f"Création d'un nouveau audit.")
    return create_audit(db, audit_data)

@router.get("/audits/{audit_id}", response_model=AuditResponse, summary="Lister les audits par ID", description="Récupère un audit par son ID.)")
def read_audit(audit_id: int, db: Session = Depends(get_db)):
    logger.info(f"Lecture de l'audit ID {audit_id}")
    audit = get_audit(db, audit_id)
    if not audit:
        logger.warning(f"Audit ID {audit_id} non trouvée")
        raise HTTPException(status_code=404, detail="Audit non trouvée")
    return audit

@router.get("/audits/", response_model=List[AuditResponse], summary="Lister les audits", description="Récupère la liste de touts les audits.")
def read_affects(db: Session = Depends(get_db)):
    logger.info("Lecture de touts les audits")
    return list_audits(db)
