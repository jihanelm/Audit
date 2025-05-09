from datetime import date
from typing import Optional, List

from pydantic import BaseModel

from backend.schemas.auditeur import AuditeurSchema, AuditeurResponse
from backend.schemas.ip import IPSchema, IPResponse

class AffectSchema(BaseModel):
    demande_audit_id: int
    prestataire_id: int
    type_audit: str
    auditeurs: List[AuditeurSchema]  # <--- ici sans ID
    ips: List[IPSchema]

class AffectResponse(BaseModel):
    id: Optional[int]
    demande_audit_id: int
    prestataire_id: int
    type_audit: str
    auditeurs: List[AuditeurResponse]  # <--- ici avec ID
    ips: List[IPResponse]
    date_affectation: date
    affectationpath: Optional[str] = None

    class Config:
        from_attributes = True