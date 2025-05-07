from io import BytesIO
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload
from backend.models.plan import Plan
from backend.models.vulnerability import Vulnerability
from backend.schemas.plan import PlanUpdate

from collections import defaultdict

from backend.schemas.vulnerability import VulnerabiliteUpdate
from log_config import setup_logger

logger = setup_logger()

async def process_uploaded_plan(file: UploadFile, db: Session):
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Format de fichier non supporté.")

    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df.replace({np.nan: None}, inplace=True)

        required_columns = {
            "ref", "application", "type_application", "type_audit",
            "date_realisation", "date_cloture", "date_rapport",
            "nb_vulnerabilites", "niveau_securite", "commentaire_dcsg",
            "commentaire_cp", "taux_remediation",
            "titre", "criticite", "pourcentage_remediation", "statut_remediation", "actions"
        }

        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes : {required_columns - set(df.columns)}")

        # Group by ref
        grouped = defaultdict(list)
        for index, row in df.iterrows():
            if not row.get("ref") or not row.get("date_realisation"):
                logger.warning(f"Ligne ignorée : ref ou date_realisation manquante à l'index {index}")
                continue
            grouped[row["ref"]].append(row.to_dict())

        df = df.dropna(subset=['ref', 'date_realisation'])

        for ref, rows in grouped.items():
            first_row = rows[0]

            try:
                date_realisation = pd.to_datetime(first_row["date_realisation"], dayfirst=True, errors="coerce")
                if pd.isnull(date_realisation):
                    raise ValueError("Date de réalisation invalide.")
            except Exception as e:
                raise HTTPException(status_code=400,
                        detail=f"Erreur de date de réalisation pour le plan '{ref}' : {str(e)}")

            plan = Plan(
                ref=ref,
                application=first_row["application"],
                type_application=first_row["type_application"],
                type_audit=first_row["type_audit"],
                date_realisation=date_realisation,
                date_cloture=pd.to_datetime(first_row.get("date_cloture")) if first_row.get("date_cloture") else None,
                date_rapport=pd.to_datetime(first_row.get("date_rapport")) if first_row.get("date_rapport") else None,
                niveau_securite=first_row.get("niveau_securite"),
                nb_vulnerabilites=first_row.get("nb_vulnerabilites"),
                taux_remediation=first_row.get("taux_remediation"),
                commentaire_dcsg=first_row.get("commentaire_dcsg"),
                commentaire_cp=first_row.get("commentaire_cp")
            )

            db.add(plan)
            db.flush()
            db.refresh(plan)

            for row in rows:
                try:
                    vuln = Vulnerability(
                        plan_id=plan.id,
                        titre=row.get("titre"),
                        criticite=row.get("criticite"),
                        pourcentage_remediation=row.get("pourcentage_remediation"),
                        statut_remediation=row.get("statut_remediation"),
                        actions=row.get("actions")
                    )
                    db.add(vuln)
                except Exception as e:
                    logger.error(f"Erreur insertion vulnérabilité pour ref {ref} : {e}")

        db.commit()
        logger.info("Plans et vulnérabilités insérés avec succès.")
        return {"message": "Importation réussie"}

    except Exception as e:
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors du traitement du fichier : {error_message}")
        raise HTTPException(status_code=500, detail="Erreur de traitement du fichier.")

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

    query = db.query(Plan).options(joinedload(Plan.vulnerabilites))

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
        vulnerabilites_data = update_fields.pop("vulnerabilites", None)

        # Mise à jour des champs du plan
        for key, value in update_fields.items():
            setattr(plan, key, value)

        # Si les vulnérabilités sont incluses
        if vulnerabilites_data is not None:
            # Supprimer les vulnérabilités existantes
            db.query(Vulnerability).filter(Vulnerability.plan_id == plan.id).delete()

            # Ajouter les nouvelles
            for vuln_data in vulnerabilites_data:
                vuln = Vulnerability(plan_id=plan.id, **vuln_data)
                db.add(vuln)

        db.commit()
        db.refresh(plan)

        logger.info(f"Plan {plan_id} et vulnérabilités mis à jour avec succès.")
        return plan

    except Exception as e:
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors de la mise à jour du plan : {error_message}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du plan.")