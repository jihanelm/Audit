from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from backend.models.associations import affect_ip

class IP(Base):
    __tablename__ = "ips"

    id = Column(Integer, primary_key=True, index=True)
    affectation_id = Column(Integer, ForeignKey("affectations.id"), nullable=False)
    adresse_ip = Column(String(50), nullable=False)

    affectation = relationship("Affectation", secondary=affect_ip, back_populates="ips")
    ports = relationship("Port", back_populates="ip", cascade="all, delete-orphan")