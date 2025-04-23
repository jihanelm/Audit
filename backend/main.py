from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from backend.routes.demande_audit import (router as demande_audit_router)
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(demande_audit_router, prefix="/audits", tags=["Audits"])


app.mount("/fichiers_attaches_audit", StaticFiles(directory="fichiers_attaches_audit"), name="fichiers_attaches_audit")
app.mount("/fiches_demandes_audit", StaticFiles(directory="fiches_demandes_audit"), name="fiches_demandes_audit")
#app.mount("/affectations_pdfs", StaticFiles(directory="affectations_pdfs"), name="affectations")

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'APP de gestion des audits"}
