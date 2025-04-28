from typing import Optional, List
from pydantic import BaseModel

from backend.schemas.auditeur import AuditeurSchema, AuditeurResponse
from backend.schemas.demande_audit import DemandeAuditBase
from backend.schemas.prestataire import PrestataireResponse


class AuditBase(BaseModel):
    demande_audit_id: int
    affectation_id: int
    prestataire_id: Optional[int] = None
    auditeurs: List[AuditeurSchema]
    duree: Optional[int] = 0
    etat: Optional[str] = "En cours"

class AuditResponse(BaseModel):
    id: int
    duree: int
    etat: str
    demande_audit: Optional[DemandeAuditBase]
    prestataire: Optional[PrestataireResponse]
    auditeurs: List[AuditeurResponse] = []

    class Config:
        from_attributes = True

