from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from backend.models.associations import audit_auditeur_association

class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    demande_audit_id = Column(Integer, ForeignKey("demandes_audits.id"), nullable=False)
    affectation_id = Column(Integer, ForeignKey("affectations.id"), nullable=False)
    prestataire_id = Column(Integer, ForeignKey("prestataires.id"))

    start_time = Column(DateTime, default=datetime.utcnow)
    last_pause_time = Column(DateTime, nullable=True)
    total_duration = Column(Float, default=0.0)  # Durée totale en jours (float)


    etat = Column(String(50), default="En cours")  # En cours, Suspendu, Terminé...

    demande_audit = relationship("Demande_Audit", back_populates="audit")
    affectation = relationship("Affectation", back_populates="audit")
    prestataire = relationship("Prestataire", back_populates="audit")
    auditeurs = relationship("Auditeur", secondary=audit_auditeur_association, back_populates="audits")
