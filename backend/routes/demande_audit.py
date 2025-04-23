from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from backend.schemas.demande_audit import DemandeAuditResponse, DemandeAuditBase
from backend.models.demande_audit import Demande_Audit
from backend.services.demande_audit import create_demande_audit, get_audit_by_id, get_all_audits

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/request", response_model=DemandeAuditResponse)
async def create_audit_request(
    type_audit: str = Form(...),
    demandeur_nom_1: str = Form(...),
    demandeur_prenom_1: str = Form(...),
    demandeur_email_1: str = Form(...),
    demandeur_phone_1: str = Form(...),
    demandeur_entite_1: str = Form(...),
    demandeur_nom_2: Optional[str] = Form(None),
    demandeur_prenom_2: Optional[str] = Form(None),
    demandeur_email_2: Optional[str] = Form(None),
    demandeur_phone_2: Optional[str] = Form(None),
    demandeur_entite_2: Optional[str] = Form(None),
    nom_app: str = Form(...),
    description: str = Form(...),
    liste_fonctionalites: str = Form(...),
    type_app: str = Form(...),
    type_app_2: str = Form(...),
    architecture_projet: bool = Form(...),
    commentaires_archi: Optional[str] = Form(None),
    protection_waf: bool = Form(...),
    commentaires_waf: Optional[str] = Form(None),
    ports: bool = Form(...),
    liste_ports: str = Form(...),
    cert_ssl_domain_name: bool = Form(...),
    commentaires_cert_ssl_domain_name: Optional[str] = Form(None),
    sys_exploitation: str = Form(...),
    logiciels_installes: Optional[str] = Form(None),
    env_tests: str = Form(...),
    donnees_prod: bool = Form(...),
    liste_si_actifs: str = Form(...),
    compte_admin: str = Form(...),
    nom_domaine: str = Form(...),
    url_app: str = Form(...),
    compte_test_profile: str = Form(...),
    urgence: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # Appeler la fonction de création de la demande d'audit
    created_demande = create_demande_audit(type_audit, demandeur_nom_1, demandeur_prenom_1, demandeur_email_1, demandeur_phone_1, demandeur_entite_1,
                                           demandeur_nom_2, demandeur_prenom_2, demandeur_email_2, demandeur_phone_2, demandeur_entite_2,
                                           nom_app, description, liste_fonctionalites, type_app, type_app_2, architecture_projet, commentaires_archi,
                                           protection_waf, commentaires_waf, ports, liste_ports, cert_ssl_domain_name,commentaires_cert_ssl_domain_name,
                                           sys_exploitation, logiciels_installes, env_tests, donnees_prod, liste_si_actifs, compte_admin,
                                           nom_domaine, url_app, compte_test_profile, urgence, files, db)

    return created_demande

@router.get("/", response_model=List[DemandeAuditResponse])
def get_audits(db: Session = Depends(get_db)):
    logger.info("Récupération de la liste des audits")
    demande_audits = get_all_audits(db)
    logger.info("Nombre d'audits récupérés: %d", len(demande_audits))
    return demande_audits


@router.get("/{audit_id}", response_model=DemandeAuditResponse)
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    logger.debug("Recherche de l'audit avec l'ID: %d", audit_id)
    demande_audit = get_audit_by_id(audit_id, db)
    if not demande_audit:
        logger.warning("Audit non trouvé pour l'ID: %d", audit_id)
        raise HTTPException(status_code=404, detail="Audit not found")
    logger.info("Audit trouvé: ID %d | Type: %s | État: %s", demande_audit.id, demande_audit.type_audit, demande_audit.etat)
    return demande_audit

@router.patch("/{audit_id}/update-etat")
def update_audit_etat(audit_id: int, etat: str, db: Session = Depends(get_db)):
    logger.info("Mise à jour de l'état de l'audit ID %d vers: %s", audit_id, etat)
    demande_audit = db.query(Demande_Audit).filter(Demande_Audit.id == audit_id).first()
    if not demande_audit:
        logger.error("Impossible de mettre à jour : audit ID %d non trouvé", audit_id)
        raise HTTPException(status_code=404, detail="Audit not found")

    demande_audit.etat = etat
    db.commit()
    db.refresh(demande_audit)
    logger.info("État mis à jour avec succès pour l'audit ID %d | Nouvel état: %s", demande_audit.id, demande_audit.etat)
    return demande_audit
