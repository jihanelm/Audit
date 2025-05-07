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
from backend.services.plan import export_plans_to_excel, get_filtered_plans, process_uploaded_plan, update_plan

from log_config import setup_logger

logger = setup_logger()

router = APIRouter()

@router.post("/upload")
async def upload_plan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await process_uploaded_plan(file, db)

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
    db_plan = Plan(**plan.dict(exclude={"vulnerabilites"}))

    if plan.vulnerabilites:
        for vuln in plan.vulnerabilites:
            db_vuln = Vulnerability(**vuln.dict())
            db_plan.vulnerabilites.append(db_vuln)

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
