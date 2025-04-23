from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from backend.models.associations import affect_auditeur


class Auditeur(Base):
    __tablename__ = "auditeurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    prestataire_id = Column(Integer, ForeignKey("prestataires.id"), nullable=False)

    prestataire = relationship("Prestataire", back_populates="auditeurs", lazy="joined")
    affectations = relationship("Affectation", secondary=affect_auditeur, back_populates="auditeurs")