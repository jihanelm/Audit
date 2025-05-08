from typing import Optional, Dict, Any, List

from pydantic import BaseModel
from datetime import date

from backend.schemas.vulnerability import VulnerabiliteCreate, VulnerabiliteResponse


class VulnerabilitySummary(BaseModel):
    critique: int
    majeure: int
    moderee: int
    mineure: int
    total: int

class PlanBase(BaseModel):
    application: Optional[str] = None
    type_application: Optional[str] = None
    type_audit: Optional[str] = None
    date_realisation: Optional[date] = None
    date_cloture: Optional[date] = None
    date_rapport: Optional[date] = None
    niveau_securite: Optional[str] = None
    nb_vulnerabilites: Optional[VulnerabilitySummary]
    taux_remediation: Optional[float] = None
    commentaire_dcsg: Optional[str] = None
    commentaire_cp: Optional[str] = None


class PlanCreate(PlanBase):
    commentaire_dcsg: Optional[str] = None
    commentaire_cp: Optional[str] = None
    vulnerabilites: Optional[List[VulnerabiliteCreate]] = []


class PlanUpdate(BaseModel):
    ref: Optional[str]
    application: str
    type_application: str
    type_audit: str
    date_realisation: Optional[date]
    date_cloture: Optional[date]
    date_rapport: Optional[date]
    niveau_securite: str
    taux_remediation: Optional[float]
    commentaire_dcsg: Optional[str]
    commentaire_cp: Optional[str]
    vulnerabilites: Optional[List[VulnerabiliteCreate]] = []

class PlanResponse(PlanBase):
    id: int
    ref: str
    vulnerabilites: List[VulnerabiliteResponse] = []

    class Config:
        from_attributes = True