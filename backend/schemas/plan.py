from typing import Optional, Dict, Any

from pydantic import BaseModel
from datetime import date

class PlanBase(BaseModel):
    #ref: str
    application: str
    type_application: str
    type_audit: str
    date_realisation: Optional[date] = None
    date_cloture: Optional[date] = None
    date_rapport: Optional[date] = None
    niveau_securite: str
    nb_vulnerabilites: str
    taux_remediation: Optional[float] = None
    commentaire_dcsg: str
    commentaire_cp: str

class PlanCreate(PlanBase):
    application: str
    type_application: str
    type_audit: str
    date_realisation: Optional[date]
    date_cloture: Optional[date]
    date_rapport: Optional[date]
    niveau_securite: str
    nb_vulnerabilites: str
    taux_remediation: Optional[float]
    commentaire_dcsg: Optional[str] = None
    commentaire_cp: Optional[str] = None

class PlanUpdate(BaseModel):
    ref: Optional[str] = None
    application: str
    type_application: str
    type_audit: str
    date_realisation: Optional[date]
    date_cloture: Optional[date]
    date_rapport: Optional[date]
    niveau_securite: str
    nb_vulnerabilites: str
    taux_remediation: Optional[float]
    commentaire_dcsg: Optional[str]
    commentaire_cp: Optional[str]

class PlanResponse(PlanBase):
    id: int
    ref: str

    class Config:
        from_attributes = True

