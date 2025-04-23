from typing import Optional

from pydantic import BaseModel


class PrestataireSchema(BaseModel):
    nom: str

class PrestataireResponse(PrestataireSchema):
    id: Optional[int]
    class Config:
        from_attributes = True
