from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from backend.models.associations import audit_auditeur_association


class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    demande_audit_id = Column(Integer, ForeignKey("demandes_audits.id"), nullable=False)
    affectation_id = Column(Integer, ForeignKey("affectations.id"), nullable=False)
    prestataire_id = Column(Integer, ForeignKey("prestataires.id"))

    duree = Column(Integer, default=0)  # durée en secondes ou minutes
    etat = Column(String(50), default="En cours")  # En cours, Suspendu, Terminé...

    demande_audit = relationship("Demande_Audit", back_populates="audit")
    affectation = relationship("Affectation", back_populates="audit")
    prestataire = relationship("Prestataire", back_populates="audit")
    auditeurs = relationship(
        "Auditeur",
        secondary=audit_auditeur_association,
        back_populates="audits"
    )
