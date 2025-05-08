from datetime import datetime, date
from io import BytesIO
from typing import Optional, List

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload
from backend.models.plan import Plan
from backend.models.vulnerability import Vulnerability
from backend.schemas.plan import PlanUpdate, VulnerabilitySummary, PlanResponse

from collections import defaultdict, Counter

from backend.schemas.vulnerability import VulnerabiliteUpdate, VulnerabiliteResponse
from log_config import setup_logger

logger = setup_logger()

def generate_plan_ref(session: Session, date_realisation: date) -> str:
    year = date_realisation.year
    total_existing = session.query(func.count()).filter(
        func.extract('year', Plan.date_realisation) == year
    ).scalar() or 0

    letter_index = total_existing // 99
    if letter_index >= 26:
        raise ValueError("Trop de plans pour l'année !")

    letter = chr(ord('A') + letter_index)
    number = (total_existing % 99) + 1
    return f"{year}_{letter}_{number:02d}"

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

        # Nettoyage
        df = df.dropna(subset=['ref', 'date_realisation'])

        grouped = defaultdict(list)
        for index, row in df.iterrows():
            grouped[row["ref"]].append(row.to_dict())

        for ref, rows in grouped.items():
            first_row = rows[0]
            try:
                date_realisation = pd.to_datetime(first_row["date_realisation"], dayfirst=True, errors="coerce")
                if pd.isnull(date_realisation):
                    raise ValueError("Date de réalisation invalide.")

                plan_ref = generate_plan_ref(db, date_realisation)

                plan = Plan(
                    ref=plan_ref,
                    application=first_row["application"],
                    type_application=first_row["type_application"],
                    type_audit=first_row["type_audit"],
                    date_realisation=date_realisation,
                    date_cloture=pd.to_datetime(first_row.get("date_cloture")) if first_row.get("date_cloture") else None,
                    date_rapport=pd.to_datetime(first_row.get("date_rapport")) if first_row.get("date_rapport") else None,
                    niveau_securite=first_row.get("niveau_securite"),
                    taux_remediation=first_row.get("taux_remediation"),
                    commentaire_dcsg=first_row.get("commentaire_dcsg"),
                    commentaire_cp=first_row.get("commentaire_cp")
                )

                db.add(plan)
                db.flush()
                db.refresh(plan)

                for row in rows:
                    vuln = Vulnerability(
                        plan_id=plan.id,
                        titre=row.get("titre"),
                        criticite=row.get("criticite"),
                        pourcentage_remediation=row.get("pourcentage_remediation"),
                        statut_remediation=row.get("statut_remediation"),
                        actions=row.get("actions")
                    )
                    db.add(vuln)

                db.flush()
                vulnerabilites = db.query(Vulnerability).filter_by(plan_id=plan.id).all()
                summary = compute_vulnerability_summary(vulnerabilites)
                plan.nb_vulnerabilites = VulnerabilitySummary(**compute_vulnerability_summary(vulnerabilites)).dict()
                plan.taux_remediation = compute_taux_remediation(vulnerabilites)

                db.commit()

            except Exception as e:
                logger.error(f"Erreur insertion vulnérabilité pour ref {ref} : {e}")
                db.rollback()

        logger.info("Plans et vulnérabilités insérés avec succès.")
        return {"message": "Importation réussie"}

    except Exception as e:
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors du traitement du fichier : {error_message}")
        raise HTTPException(status_code=500, detail="Erreur de traitement du fichier.")

def export_plans_to_excel(
        db: Session,
        ref: Optional[str] = None,
        application: Optional[str] = None,
        type_audit: Optional[str] = None,
        niveau_securite: Optional[str] = None,
        # Filtres exacts
        date_realisation: Optional[str] = None,
        date_cloture: Optional[str] = None,
        date_rapport: Optional[str] = None,
        # Filtres par année/mois
        realisation_year: Optional[int] = None,
        realisation_month: Optional[int] = None,
        cloture_year: Optional[int] = None,
        cloture_month: Optional[int] = None,
        rapport_year: Optional[int] = None,
        rapport_month: Optional[int] = None,
):
    query = db.query(Plan).options(joinedload(Plan.vulnerabilites))

    if ref:
        query = query.filter(Plan.ref.ilike(f"%{ref}%"))
    if application:
        query = query.filter(Plan.application.ilike(f"%{application}%"))
    if type_audit:
        query = query.filter(Plan.type_audit == type_audit)
    if niveau_securite:
        query = query.filter(Plan.niveau_securite == niveau_securite)

    # Filtres exacts sur les dates
    if date_realisation:
        query = query.filter(Plan.date_realisation == date_realisation)
    if date_cloture:
        query = query.filter(Plan.date_cloture == date_cloture)
    if date_rapport:
        query = query.filter(Plan.date_rapport == date_rapport)

    # Filtres par année/mois
    if realisation_year:
        query = query.filter(extract('year', Plan.date_realisation) == realisation_year)
    if realisation_month:
        query = query.filter(extract('month', Plan.date_realisation) == realisation_month)

    if cloture_year:
        query = query.filter(extract('year', Plan.date_cloture) == cloture_year)
    if cloture_month:
        query = query.filter(extract('month', Plan.date_cloture) == cloture_month)

    if rapport_year:
        query = query.filter(extract('year', Plan.date_rapport) == rapport_year)
    if rapport_month:
        query = query.filter(extract('month', Plan.date_rapport) == rapport_month)

    plans = query.all()
    if not plans:
        return None

    combined_data = []

    for plan in plans:
        if plan.vulnerabilites:
            for vuln in plan.vulnerabilites:
                combined_data.append({
                    "ID Plan": plan.id,
                    "Réf": plan.ref,
                    "Application/Solution": plan.application,
                    "Type d'application": plan.type_application,
                    "Type d'audit": plan.type_audit,
                    "Date de realisation de la mission": plan.date_realisation,
                    "Date de cloture de la mission": plan.date_cloture,
                    "Date de communication du rapport": plan.date_rapport,
                    "Niveau de securité": plan.niveau_securite,
                    "Nombre de vulnérabilités": plan.nb_vulnerabilites,
                    "Commentaire DCSG": plan.commentaire_dcsg,
                    "Commentaire CP": plan.commentaire_cp,
                    "Titre vulnérabilité": vuln.titre,
                    "Criticité": vuln.criticite,
                    "Pourcentage de remédiation": vuln.pourcentage_remediation,
                    "Statut de remédiation": vuln.statut_remediation,
                    "Actions": vuln.actions
                })
        else:
            combined_data.append({
                "ID Plan": plan.id,
                "Réf": plan.ref,
                "Application/Solution": plan.application,
                "Type d'application": plan.type_application,
                "Type d'audit": plan.type_audit,
                "Date de realisation de la mission": plan.date_realisation,
                "Date de cloture de la mission": plan.date_cloture,
                "Date de communication du rapport": plan.date_rapport,
                "Niveau de securité": plan.niveau_securite,
                "Nombre de vulnérabilités": plan.nb_vulnerabilites,
                "Commentaire DCSG": plan.commentaire_dcsg,
                "Commentaire CP": plan.commentaire_cp,
                "Titre vulnérabilité": "",
                "Criticité": "",
                "Pourcentage de remédiation": "",
                "Statut de remédiation": "",
                "Actions": ""
            })

    file_path = f"plans_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(combined_data).to_excel(writer, sheet_name="Plans avec vulnérabilités", index=False)

    return file_path

def get_filtered_plans(
    db: Session,
    ref: Optional[str] = None,
    application: Optional[str] = None,
    type_audit: Optional[str] = None,
    niveau_securite: Optional[str] = None,
    # Filtres exacts
    date_realisation: Optional[str] = None,
    date_cloture: Optional[str] = None,
    date_rapport: Optional[str] = None,
    # Filtres par année/mois
    realisation_year: Optional[int] = None,
    realisation_month: Optional[int] = None,
    cloture_year: Optional[int] = None,
    cloture_month: Optional[int] = None,
    rapport_year: Optional[int] = None,
    rapport_month: Optional[int] = None,
):
    query = db.query(Plan).options(joinedload(Plan.vulnerabilites))

    # Filtres textuels
    if ref:
        query = query.filter(Plan.ref.ilike(f"%{ref}%"))
    if application:
        query = query.filter(Plan.application.ilike(f"%{application}%"))
    if type_audit:
        query = query.filter(Plan.type_audit == type_audit)
    if niveau_securite:
        query = query.filter(Plan.niveau_securite == niveau_securite)

    # Filtres exacts sur les dates
    if date_realisation:
        query = query.filter(Plan.date_realisation == date_realisation)
    if date_cloture:
        query = query.filter(Plan.date_cloture == date_cloture)
    if date_rapport:
        query = query.filter(Plan.date_rapport == date_rapport)

    # Filtres par année/mois
    if realisation_year:
        query = query.filter(extract('year', Plan.date_realisation) == realisation_year)
    if realisation_month:
        query = query.filter(extract('month', Plan.date_realisation) == realisation_month)

    if cloture_year:
        query = query.filter(extract('year', Plan.date_cloture) == cloture_year)
    if cloture_month:
        query = query.filter(extract('month', Plan.date_cloture) == cloture_month)

    if rapport_year:
        query = query.filter(extract('year', Plan.date_rapport) == rapport_year)
    if rapport_month:
        query = query.filter(extract('month', Plan.date_rapport) == rapport_month)

    return query.all()

def update_plan(db: Session, plan_id: int, updated_data: PlanUpdate, vulnerabilites=None):
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
            new_vulns = []
            for vuln_data in vulnerabilites_data:
                vuln = Vulnerability(plan_id=plan.id, **vuln_data)
                db.add(vuln)
                new_vulns.append(vuln)

            db.flush()  # s'assurer que les vulnérabilités sont bien insérées avant résumé

            # Mettre à jour les champs résumés à partir des nouvelles vulnérabilités
            summary = compute_vulnerability_summary(new_vulns)
            plan.nb_vulnerabilites = dict(summary)
            plan.taux_remediation = compute_taux_remediation(new_vulns)

        db.commit()
        db.refresh(plan)

        logger.info(f"Plan {plan_id} et vulnérabilités mis à jour avec succès.")
        return plan

    except Exception as e:
        db.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Erreur lors de la mise à jour du plan : {error_message}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du plan.")

def serialize_plan(plan: Plan) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        ref=plan.ref,
        application=plan.application,
        type_application=plan.type_application,
        type_audit=plan.type_audit,
        date_realisation=plan.date_realisation,
        date_cloture=plan.date_cloture,
        date_rapport=plan.date_rapport,
        niveau_securite=plan.niveau_securite,
        taux_remediation=plan.taux_remediation,
        commentaire_dcsg=plan.commentaire_dcsg,
        commentaire_cp=plan.commentaire_cp,
        nb_vulnerabilites=VulnerabilitySummary(**plan.nb_vulnerabilites)
        if isinstance(plan.nb_vulnerabilites, dict) else None,

        vulnerabilites=[
            VulnerabiliteResponse(
                id=v.id,
                titre=v.titre,
                criticite=v.criticite,
                pourcentage_remediation=v.pourcentage_remediation,
                statut_remediation=v.statut_remediation,
                actions=v.actions
            ) for v in plan.vulnerabilites
        ]
    )

def compute_vulnerability_summary(vulnerabilities):
    criticity_counts = Counter([v.criticite for v in vulnerabilities if v.criticite])
    return {
        "critique": criticity_counts.get("critique", 0),
        "majeure": criticity_counts.get("majeure", 0),
        "moderee": criticity_counts.get("moderee", 0),
        "mineure": criticity_counts.get("mineure", 0),
        "total": len(vulnerabilities)
    }

def compute_taux_remediation(vulnerabilites: List[Vulnerability]) -> float:
    valeurs = [v.pourcentage_remediation for v in vulnerabilites if v.pourcentage_remediation is not None]
    if not valeurs:
        return 0.0
    return round(sum(valeurs) / len(valeurs), 2)
