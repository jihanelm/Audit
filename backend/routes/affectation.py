from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List

from backend.models.prestataire import Prestataire
from backend.models.ip import IP
from backend.schemas.affectation import AffectSchema, AffectResponse
from backend.schemas.auditeur import AuditeurSchema, AuditeurResponse
from backend.schemas.prestataire import PrestataireSchema, PrestataireResponse
from backend.schemas.ip import IPResponse
from backend.services.affectation import create_affect, get_affect, list_affects, create_auditeur, list_auditeurs, \
    create_prestataire, delete_auditeur, update_auditeur

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/affects/", response_model=AffectResponse, summary="Creer une affectation", description="Permet de creer une affectation")
def create_affectation(affect_data: AffectSchema, db: Session = Depends(get_db)):
    logger.debug(f"Création d'une nouvelle affectation pour demande_audit_id {affect_data.demande_audit_id}")
    logger.info(f"Création d'une nouvelle affectation")
    return create_affect(db, affect_data)

@router.get("/affects/{affect_id}", response_model=AffectResponse, summary="Lister les affectations par ID", description="Récupère une affectation par son ID avec les informations associées (auditeurs, prestataires, audit, etc.)")
def read_affect(affect_id: int, db: Session = Depends(get_db)):
    logger.info(f"Lecture de l'affectation ID {affect_id}")
    affect = get_affect(db, affect_id)
    if not affect:
        logger.warning(f"Affectation ID {affect_id} non trouvée")
        raise HTTPException(status_code=404, detail="Affectation non trouvée")
    return affect

@router.get("/affects/", response_model=List[AffectResponse], summary="Lister les affectations", description="Récupère la liste de toutes les affectations avec les informations associées (auditeurs, prestataires, audit...)")
def read_affects(db: Session = Depends(get_db)):
    logger.info("Lecture de toutes les affectations")
    return list_affects(db)

# Endpoints pour la gestion des auditeurs
@router.post("/auditeurs/", response_model=AuditeurResponse, summary="Creer les auditeurs", description="Permet de creer les auditeurs")
def create_auditor(auditeur_data: AuditeurSchema, db: Session = Depends(get_db)):
    logger.info(f"Création d’un auditeur: {auditeur_data.nom} {auditeur_data.prenom}")
    return create_auditeur(db, auditeur_data)

@router.post("/prestataires/", response_model=PrestataireResponse, summary="creer les prestataires", description="Permet de creer les prestataires")
def create_prestat(prestataire_data: PrestataireSchema, db: Session = Depends(get_db)):
    logger.info(f"Création du prestataire: {prestataire_data.nom}")
    return create_prestataire(db, prestataire_data)

@router.get("/auditeurs/", response_model=List[AuditeurResponse], summary="Lister les auditeurs", description="Récupère la liste de toutes les auditeurs avec les informations associées (nom, prenom, email...)")
def read_auditors(db: Session = Depends(get_db)):
    logger.info("Lecture de la liste des auditeurs")
    return list_auditeurs(db)

# Endpoints pour la gestion des prestataires
@router.get("/prestataires/", response_model=List[PrestataireResponse], summary="Lister les prestataires", description="Récupère la liste de toutes les prestataires")
def read_prestataires(db: Session = Depends(get_db)):
    logger.info("Lecture de la liste des prestataires")
    return db.query(Prestataire).all()

# Endpoints pour la gestion des IPs
@router.get("/ips/", response_model=List[IPResponse], summary="Lister les IPs", description="Récupère la liste de toutes les IPs et leurs ports")
def read_ips(db: Session = Depends(get_db)):
    logger.info("Lecture de la liste des IPs")
    return db.query(IP).all()

@router.delete("/auditeurs/{auditeur_id}", response_model=AuditeurResponse, summary="Supprimer un auditeur par ID", description="Permet de supprimer un auditeur par son ID de la liste de auditeurs")
def remove_auditeur(auditeur_id: int, db: Session = Depends(get_db)):
    logger.info(f"Suppression de l’auditeur ID {auditeur_id}")
    auditeur = delete_auditeur(db, auditeur_id)
    if not auditeur:
        logger.warning(f"Auditeur ID {auditeur_id} non trouvé pour suppression")
        raise HTTPException(status_code=404, detail="Auditeur not found")
    return auditeur

@router.put("/auditeurs/{auditeur_id}", response_model=AuditeurResponse, summary="Modifier un auditeur", description="Permet de modifier les informations d'un auditeur deja existant")
def update_auditeur_endpoint(auditeur_id: int, auditeur_data: AuditeurSchema, db: Session = Depends(get_db)):
    logger.info(f"Mise à jour de l’auditeur ID {auditeur_id}")
    auditeur = update_auditeur(db, auditeur_id, auditeur_data)
    if not auditeur:
        logger.warning(f"Auditeur ID {auditeur_id} non trouvé pour mise à jour")
        raise HTTPException(status_code=404, detail="Auditeur non trouvé")
    return auditeur