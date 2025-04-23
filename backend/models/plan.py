from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, event, func
from sqlalchemy.orm import relationship, Session
from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String(50), unique=True, index=True)
    type_audit = Column(String(100), nullable=False)
    date_debut = Column(Date, nullable=False)
    date_realisation = Column(Date, nullable=True)
    duree = Column(Integer, nullable=False)  # En jours
    date_fin = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    remarques = Column(String(255), nullable=True)

    extra_data = Column(JSON, nullable=True)

    audit_id = Column(Integer, ForeignKey("audits.id"))
    audit = relationship("Audit", back_populates="plans")


@event.listens_for(Plan, "before_insert")
def generate_ref(mapper, connection, target):
    session = Session(bind=connection)

    year = target.date_debut.year

    # Compter les plans déjà créés pour cette année
    count_query = (
        session.query(func.count())
        .select_from(Plan)
        .filter(func.year(Plan.date_debut) == year)
    )

    total_existing = count_query.scalar() or 0

    # Calcul de la lettre : A, B, C, ...
    letter_index = total_existing // 99
    if letter_index >= 26:
        raise ValueError("Trop de plans pour l'année ! (limité à 26 lettres A-Z)")

    letter = chr(ord('A') + letter_index)

    # Calcul du numéro (1 à 99)
    plan_number = (total_existing % 99) + 1

    # Générer la ref
    target.ref = f"{year}_{letter}_{plan_number:02d}"

    session.close()