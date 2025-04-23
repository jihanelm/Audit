from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    port = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)

    ip_id = Column(Integer, ForeignKey("ips.id"))
    ip = relationship("IP", back_populates="ports")
