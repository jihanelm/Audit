from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.audit import Audit
from backend.schemas.audit import AuditResponse, AuditBase, EtatUpdate
from backend.services.audit import create_audit, get_audit, list_audits, change_audit_etat
from database import get_db
from typing import List
from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/audits/", response_model=AuditResponse)
def create_audit_route(audit_data: AuditBase, db: Session = Depends(get_db)):
    return create_audit(db, audit_data)

@router.get("/audits/{audit_id}", response_model=AuditResponse)
def read_audit(audit_id: int, db: Session = Depends(get_db)):
    audit = get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit

@router.get("/audits/", response_model=List[AuditResponse])
def read_affects(db: Session = Depends(get_db)):
    return list_audits(db)

@router.patch("/audits/{audit_id}/etat", response_model=AuditResponse)
def update_etat_audit(audit_id: int, etat_update: EtatUpdate, db: Session = Depends(get_db)):
    return change_audit_etat(db, audit_id, etat_update.new_etat)

@router.get("/audit/audits/{id}/duration")
def get_audit_duration(id: int, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")

    duration = audit.total_duration
    if audit.etat == "En cours" and audit.start_time:
        elapsed_seconds = (datetime.utcnow() - audit.start_time).total_seconds()
        duration += elapsed_seconds / 86400

    return {"duration": round(duration, 2)}
