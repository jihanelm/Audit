from typing import Optional

from pydantic import BaseModel, EmailStr

class AuditeurSchema(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    phone: str
    prestataire_id: int

class AuditeurResponse(AuditeurSchema):
    id: Optional[int]

    class Config:
        from_attributes = True

