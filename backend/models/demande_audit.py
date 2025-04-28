from sqlalchemy import Column, Integer, String, Date, Boolean, func, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType

from database import Base
from datetime import date

class Demande_Audit(Base):
    __tablename__ = "demandes_audits"

    id = Column(Integer, primary_key=True, index=True)
    type_audit = Column(String(100), nullable=False)
    etat = Column(String(50), default="En attente", index=True)
    date_creation = Column(Date, default=date.today, nullable=False, index=True)
    updated_at = Column(Date, onupdate=func.current_date())

    # Identification du demandeur
    demandeur_nom_1 = Column(String(100), nullable=False)
    demandeur_prenom_1 = Column(String(100), nullable=False)
    demandeur_email_1 = Column(EmailType, nullable=False)
    demandeur_phone_1 = Column(String(20), nullable=False)
    demandeur_entite_1 = Column(String(100), nullable=False)
    demandeur_nom_2 = Column(String(100), nullable=False)
    demandeur_prenom_2 = Column(String(100), nullable=False)
    demandeur_email_2 = Column(EmailType, nullable=False)
    demandeur_phone_2 = Column(String(20), nullable=False)
    demandeur_entite_2 = Column(String(100), nullable=False)

    # Application ou Solution
    nom_app = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    liste_fonctionalites = Column(Text, nullable=False)
    type_app = Column(String(100), nullable=False)
    type_app_2 = Column(String(100), nullable=False)

    # Exigence techniques
    architecture_projet = Column(Boolean, nullable=False) # True = Existe
    commentaires_archi = Column(Text, nullable=False)
    protection_waf = Column(Boolean, nullable=False) # True = Existe
    commentaires_waf = Column(Text, nullable=False)
    ports = Column(Boolean, nullable=False)
    liste_ports = Column(Text, nullable=False)
    cert_ssl_domain_name = Column(Boolean, nullable=False)
    commentaires_cert_ssl_domain_name = Column(Text, nullable=False)

    # Prerequis techniques
    sys_exploitation = Column(String(100), nullable=False)
    logiciels_installes = Column(Text, nullable=False)
    env_tests = Column(String(100), nullable=False)
    donnees_prod = Column(Boolean, nullable=False)
    liste_si_actifs = Column(Text, nullable=False)
    compte_admin = Column(String(150), nullable=False)
    nom_domaine = Column(String(100), nullable=False)
    url_app = Column(String(100), nullable=False)
    compte_test_profile = Column(Text, nullable=False)

    urgence = Column(String(50), nullable=False)

    fichiers_attaches = Column(JSON, nullable=True)
    fiche_demande_path = Column(String(255), nullable=True)

    affectations = relationship("Affectation", back_populates="demande_audit")
    audit = relationship("Audit", back_populates="demande_audit")
    #plans = relationship("Plan", back_populates="audit")

    def __repr__(self):
        return f"<Audit(id={self.id}, etat={self.etat})>"
