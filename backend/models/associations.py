from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import Session

from database import Base
#from backend.models.plan import Plan

affect_auditeur = Table(
    "affect_auditeur",
    Base.metadata,
    Column("affectation_id", Integer, ForeignKey("affectations.id"), primary_key=True),
    Column("auditeur_id", Integer, ForeignKey("auditeurs.id"), primary_key=True)
)

audit_auditeur_association = Table(
    "audit_auditeur_association",
    Base.metadata,
    Column("audit_id", Integer, ForeignKey("audits.id")),
    Column("auditeur_id", Integer, ForeignKey("auditeurs.id")),
)

affect_ip = Table(
    "affect_ip",
    Base.metadata,
    Column("affectation_id", Integer, ForeignKey("affectations.id"), primary_key=True),
    Column("ip_id", Integer, ForeignKey("ips.id"), primary_key=True)
)

"""def audits_plans(db: Session):

    plans = db.query(Plan).filter(Plan.audit_id.is_(None)).all()

    for plan in plans:
        audit = db.query(Audit).filter(
            Audit.type == plan.type_audit,
            Audit.date == plan.date_debut
        ).first()

        if audit:
            plan.audit_id = audit.id
            db.commit()
            db.refresh(plan)"""