import os
from typing import Optional, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from database import get_db
from backend.models.audit import Audit
from backend.models.plan import Plan
from backend.schemas.plan import PlanResponse, PlanCreate, PlanUpdate
from backend.services.plan import export_plans_to_excel, get_filtered_plans, process_uploaded_plan, update_plan

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/upload")
async def upload_plan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await process_uploaded_plan(file, db)

"""@router.put("/plans/{plan_id}/associate_audit/{audit_id}")
def associate_audit(plan_id: int, audit_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    audit = db.query(Audit).filter(Audit.id == audit_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")

    plan.audit_id = audit.id
    db.commit()
    db.refresh(plan)

    return {"message": "Audit associé avec succès", "plan_id": plan.id, "audit_id": audit.id}"""

@router.get("/plans/download/")
def download_plans(
    db: Session = Depends(get_db),
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2000, le=2100),
):
    file_path = export_plans_to_excel(db, month, year)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Aucun plan trouvé pour cette période")

    return FileResponse(file_path, filename=os.path.basename(file_path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/plans/", response_model=List[PlanResponse])
def get_plans(
        db: Session = Depends(get_db),
        month: Optional[int] = None,
        year: Optional[int] = None,
        type_audit: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        rapport_date: Optional[str] = None
) -> Session:
    plans = get_filtered_plans(
        db,
        month=month,
        year=year,
        rapport_date=rapport_date,
        type_audit=type_audit,
        start_date=start_date,
        end_date=end_date
    )

    return plans

@router.post("/plan/", response_model=PlanResponse)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/plans/{plan_id}", response_model=PlanUpdate)
def update_plan_endpoint(
    plan_id: int,
    updated_data: PlanUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    return update_plan(db, plan_id, updated_data)
