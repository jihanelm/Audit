from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from backend.models.associations import affect_auditeur, affect_ip
from datetime import date

class Affectation(Base):
    __tablename__ = "affectations"

    id = Column(Integer, primary_key=True, index=True)
    demande_audit_id = Column(Integer, ForeignKey("demandes_audits.id"), nullable=False)
    date_affectation = Column(Date, default=date.today, nullable=False)
    affectationpath = Column(String(255), nullable=True)
    prestataire_id = Column(Integer, ForeignKey("prestataires.id"))

    demande_audit = relationship("Demande Audit", back_populates="affectationss")
    auditeurs = relationship("Auditeur", secondary=affect_auditeur, back_populates="affects")
    prestataire = relationship("Prestataire", back_populates="affectations")
    ips = relationship("IP", secondary=affect_ip, back_populates="affectation")