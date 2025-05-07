from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes.demande_audit import (router as demande_audit_router)
from backend.routes.affectation import (router as affectation_router)
from backend.routes.audit import (router as audit_router)
from backend.routes.plan import (router as plan_router)
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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