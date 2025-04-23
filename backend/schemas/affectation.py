import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from backend.schemas.auditeur import AuditeurSchema
from backend.schemas.ip import IPSchema


class AffectSchema(BaseModel):
    demande_audit_id: int
    prestataire_id: int
    auditeurs: List[AuditeurSchema]
    ips: List[IPSchema]


class AffectResponse(AffectSchema):
    id: Optional[int]
    date_affectation: date
    affectationpath: Optional[str] = None

    class Config:
        from_attributes = True