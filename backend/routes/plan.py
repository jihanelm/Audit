import os
from typing import Optional, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from backend.models.vulnerability import Vulnerability
from database import get_db
from backend.models.audit import Audit
from backend.models.plan import Plan
from backend.schemas.plan import PlanResponse, PlanCreate, PlanUpdate
from backend.services.plan import export_plans_to_excel, get_filtered_plans, process_uploaded_plan, update_plan, \
    compute_vulnerability_summary, serialize_plan, compute_taux_remediation

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/upload")
async def upload_plan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await process_uploaded_plan(file, db)

@router.get("/plans/download/")
def export_plans(db: Session = Depends(get_db),
        ref: Optional[str] = None,
        application: Optional[str] = None,
        type_audit: Optional[str] = None,
        niveau_securite: Optional[str] = None,

        # Filtres exacts sur les dates
        date_realisation: Optional[str] = None,
        date_cloture: Optional[str] = None,
        date_rapport: Optional[str] = None,

        # Filtres par année/mois pour chaque type de date
        realisation_year: Optional[int] = None,
        realisation_month: Optional[int] = None,
        cloture_year: Optional[int] = None,
        cloture_month: Optional[int] = None,
        rapport_year: Optional[int] = None,
        rapport_month: Optional[int] = None):
    file_path = export_plans_to_excel(db, ref, application, type_audit, niveau_securite, date_realisation, date_cloture, date_rapport, realisation_year,
                                      realisation_month, cloture_year, cloture_month, rapport_year, rapport_month)

    if file_path is None:
        raise HTTPException(status_code=404, detail="Aucun plan trouvé à exporter.")

    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_path.split("/")[-1])

@router.get("/plans/", response_model=List[PlanResponse])
def get_plans(
    db: Session = Depends(get_db),
    ref: Optional[str] = None,
    application: Optional[str] = None,
    type_audit: Optional[str] = None,
    niveau_securite: Optional[str] = None,

    # Filtres exacts sur les dates
    date_realisation: Optional[str] = None,
    date_cloture: Optional[str] = None,
    date_rapport: Optional[str] = None,

    # Filtres par année/mois pour chaque type de date
    realisation_year: Optional[int] = None,
    realisation_month: Optional[int] = None,
    cloture_year: Optional[int] = None,
    cloture_month: Optional[int] = None,
    rapport_year: Optional[int] = None,
    rapport_month: Optional[int] = None
):
    plans = get_filtered_plans(
        db=db,
        ref=ref,
        application=application,
        type_audit=type_audit,
        niveau_securite=niveau_securite,
        date_realisation=date_realisation,
        date_cloture=date_cloture,
        date_rapport=date_rapport,
        realisation_year=realisation_year,
        realisation_month=realisation_month,
        cloture_year=cloture_year,
        cloture_month=cloture_month,
        rapport_year=rapport_year,
        rapport_month=rapport_month
    )

    return [serialize_plan(p) for p in plans]

@router.post("/plan/", response_model=PlanResponse)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    db_plan = Plan(**plan.dict(exclude={"vulnerabilites"}))
    db.add(db_plan)
    db.flush()
    db.commit()
    db.refresh(db_plan)

    if plan.vulnerabilites:
        for vuln in plan.vulnerabilites:
            db_vuln = Vulnerability(plan_id=db_plan.id, **vuln.dict())
            db.add(db_vuln)
        db.flush()
        vulns = db.query(Vulnerability).filter_by(plan_id=db_plan.id).all()
        db_plan.nb_vulnerabilites = compute_vulnerability_summary(vulns)
        db_plan.taux_remediation = compute_taux_remediation(vulns)
        db.commit()
        db.refresh(db_plan)

    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan_endpoint(
    plan_id: int,
    updated_data: PlanUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    return update_plan(db, plan_id, updated_data)

