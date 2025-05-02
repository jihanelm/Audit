from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from backend.routes.demande_audit import (router as demande_audit_router)
from backend.routes.affectation import (router as affectation_router)
from backend.routes.audit import (router as audit_router)
from backend.routes.plan import (router as plan_router)
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

from fastapi import FastAPI, UploadFile, File
import pandas as pd
import yaml
from openpyxl import load_workbook
import tempfile
import shutil
import os

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(demande_audit_router, prefix="/audits", tags=["Demandes Audits"])
app.include_router(affectation_router, prefix="/affectation", tags=["Affectations"])
app.include_router(audit_router, prefix="/audit", tags=["Audits"])
app.include_router(plan_router, prefix="/plan", tags=["Plans"])


app.mount("/fichiers_attaches_audit", StaticFiles(directory="fichiers_attaches_audit"), name="fichiers_attaches_audit")
app.mount("/fiches_demandes_audit", StaticFiles(directory="fiches_demandes_audit"), name="fiches_demandes_audit")
app.mount("/fichiers_affectations", StaticFiles(directory="fichiers_affectations"), name="fichiers_affectations")

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'APP de gestion des audits"}



def lire_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def traiter_excel(fichier_excel_path: str, config_path: str, fields_path: str):
    config = lire_yaml(config_path)
    fields = lire_yaml(fields_path)

    # Lecture page de garde
    wb = load_workbook(fichier_excel_path, data_only=True)
    sheet_pg = wb[config["page_de_garde"]["sheet"]]
    page_de_garde = {
        champ: sheet_pg[cell].value
        for champ, cell in config["page_de_garde"]["fields"].items()
    }

    # Lecture feuille des données
    df = pd.read_excel(fichier_excel_path, sheet_name="Plans", engine="openpyxl")

    # Appliquer le mapping principal
    df = df.rename(columns=fields["fields_mapping"])
    donnees = df[list(fields["fields_mapping"].values())]

    # Mapping vulnérabilités
    vuln_map = fields.get("vulnerabilite_mapping", {})
    cols_dispo = [col for col in vuln_map if col in df.columns]
    df.rename(columns={col: vuln_map[col] for col in cols_dispo}, inplace=True)
    vuln_final_cols = list(vuln_map.values())
    vulnerabilites = df[vuln_final_cols] if all(col in df.columns for col in vuln_final_cols) else pd.DataFrame()

    return {
        "page_de_garde": page_de_garde,
        "donnees": donnees.to_dict(orient="records"),
        "vulnerabilites": vulnerabilites.to_dict(orient="records"),
    }

@app.post("/import-excel/")
async def import_excel(
    file: UploadFile = File(...),
    config_path: str = "chemin/vers/excel_config.yaml",
    fields_path: str = "chemin/vers/plan_fields.yaml"
):
    # Sauvegarder temporairement le fichier reçu
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        resultat = traiter_excel(tmp_path, config_path, fields_path)
        return resultat
    finally:
        os.remove(tmp_path)
