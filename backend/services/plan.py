from io import BytesIO
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import extract
from sqlalchemy.orm import Session
from backend.models.plan import Plan
from backend.schemas.plan import PlanUpdate

from datetime import date

from log_config import setup_logger

logger = setup_logger()

async def process_uploaded_plan(file: UploadFile, db: Session):
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Veuillez uploader un fichier Excel.")

    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        required_columns = {"ref", "application", "type_application", "type_audit",
            "date_realisation", "date_cloture", "date_rapport", "nb_vulnerabilites",
            "niveau_securite", "commentaire_dcsg", "commentaire_cp", "taux_remediation"}

        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes: {required_columns - set(df.columns)}")

        plans_to_insert = []
        for _, row in df.iterrows():
            extra_fields = {col: row[col] for col in df.columns if col not in required_columns}

            plan = Plan(
                ref=row["ref"],
                application=row["application"],
                type_application=row["type_application"],
                type_audit=row["type_audit"],
                date_realisation=row.get("date_realisation"),
                date_cloture=row.get("date_cloture"),
                date_rapport=row.get("date_rapport"),
                niveau_securite=row.get("niveau_securite"),
                nb_vulnerabilites=row.get("nb_vulnerabilites"),
                taux_remediation=row.get("taux_remediation"),
                commentaire_dcsg=row.get("commentaire_dcsg"),
                commentaire_cp=row.get("commentaire_cp")

            )
            plans_to_insert.append(plan)

        db.bulk_save_objects(plans_to_insert)
        db.commit()

        logger.info("Plans inserted successfully")
        return ""

    except Exception as e:
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors du traitement du fichier : {error_message}")
        raise HTTPException(status_code=500, detail=f"Erreur de traitement du fichier")

def export_plans_to_excel(db: Session, month: int = None, year: int = None):
    query = db.query(Plan)

    if year:
        query = query.filter(extract('year', Plan.date_realisation) == year)
    if month:
        query = query.filter(extract('month', Plan.date_realisation) == month)

    plans = query.all()

    if not plans:
        return None

    data = []
    for plan in plans:
        row = {
            "ID": plan.id,
            "Réf": plan.ref,
            "Application/Solution": plan.application,
            "Type d'application": plan.type_application,
            "Type d'udit": plan.type_audit,
            "Date de realisation de la mission": plan.date_realisation,
            "Date de cloture de la mission": plan.date_cloture,
            "Date de communication du rapport": plan.date_rapport,
            "Niveau de securité": plan.niveau_securite,
            "Nombre des vulnérabilités soulevées": plan.nb_vulnerabilites,
            "Commentaire DCSG": plan.commentaire_dcsg,
            "Commentaire CP": plan.commentaire_cp
        }

        data.append(row)

    df = pd.DataFrame(data)
    file_path = f"plans_{year}_{month}.xlsx" if month else f"plans_{year}.xlsx"
    df.to_excel(file_path, index=False)

    return file_path

def get_filtered_plans(
    db: Session,
    month: Optional[int] = None,
    year: Optional[int] = None,
    type_audit: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    rapport_date: Optional[str] = None
):
    query = db.query(Plan)

    if year:
        query = query.filter(extract('year', Plan.date_realisation) == year)
    if month:
        query = query.filter(extract('month', Plan.date_realisation) == month)
    if rapport_date:
        query = query.filter(Plan.date_rapport == rapport_date)
    if type_audit:
        query = query.filter(Plan.type_audit == type_audit)
    if start_date:
        query = query.filter(Plan.date_realisation >= start_date)
    if end_date:
        query = query.filter(Plan.date_cloture <= end_date)

    return query.all()

def update_plan(db: Session, plan_id: int, updated_data: PlanUpdate):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé.")

    try:
        update_fields = updated_data.dict(exclude_unset=True)
        for key, value in update_fields.items():
            setattr(plan, key, value)

        db.commit()
        db.refresh(plan)

        logger.info(f"Plan {plan_id} mis à jour avec succès.")
        return plan

    except Exception as e:
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors de la mise à jour du plan : {error_message}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du plan.")