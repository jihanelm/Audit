import os

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime


class DemandeAuditBase(BaseModel):
    type_audit: str

    # Identification du demandeur
    demandeur_nom_1: str
    demandeur_prenom_1: str
    demandeur_email_1: EmailStr
    demandeur_phone_1: str
    demandeur_entite_1: str
    demandeur_nom_2: Optional[str] = None
    demandeur_prenom_2: Optional[str] = None
    demandeur_email_2: Optional[EmailStr] = None
    demandeur_phone_2: Optional[str] = None
    demandeur_entite_2: Optional[str] = None

    @validator("demandeur_email_2", pre=True)
    def empty_string_to_none(cls, v):
        return v or None

    # Application ou Solution
    nom_app: str
    description: str
    liste_fonctionalites: str
    type_app: str
    type_app_2: str

    # Exigences techniques
    architecture_projet: bool
    commentaires_archi: Optional[str] = "None"
    protection_waf: bool
    commentaires_waf: Optional[str] = "None"
    ports: bool
    liste_ports: str
    cert_ssl_domain_name: bool
    commentaires_cert_ssl_domain_name: Optional[str] = "None"

    # Prérequis techniques
    sys_exploitation: str
    logiciels_installes: Optional[str] = "None"
    env_tests: str
    donnees_prod: bool
    liste_si_actifs: str
    compte_admin: str
    nom_domaine: str
    url_app: str
    compte_test_profile: str
    urgence: str

    fichiers_attaches: Optional[List[str]] = []
class DemandeAuditCreate(DemandeAuditBase):
    pass

class DemandeAuditResponse(DemandeAuditBase):
    id: int
    date_creation: date
    type_audit: str
    etat: str
    fiche_demande_path: Optional[str] = None

    @property
    def fichier_url(self):
        if self.fichiers_attaches:
            return f"http://localhost:8000/{self.fichiers_attaches[0].replace(os.sep, '/')}"
        return None

class DemandeAuditOut(DemandeAuditBase):
    id: int
    date_creation: date
    updated_at: datetime

    class Config:
        from_attributes = True
