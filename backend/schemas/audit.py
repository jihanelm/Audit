from typing import Optional, List
from pydantic import BaseModel

from backend.schemas.auditeur import AuditeurSchema, AuditeurResponse
from backend.schemas.demande_audit import DemandeAuditBase
from backend.schemas.prestataire import PrestataireResponse


class AuditBase(BaseModel):
    demande_audit_id: int
    affectation_id: int
    prestataire_id: Optional[int] = None
    auditeur_ids: List[int]

class AuditResponse(BaseModel):
    id: int
    total_duration: float  # Nombre de jours
    etat: str
    demande_audit: Optional[DemandeAuditBase]
    prestataire: Optional[PrestataireResponse]
    auditeurs: List[AuditeurResponse] = []

    class Config:
        from_attributes = True

