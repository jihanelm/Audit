from pydantic import BaseModel
from typing import Optional, List

from backend.schemas.ports import PortSchema, PortResponse


class IPSchema(BaseModel):
    adresse_ip: str
    ports: List[PortSchema]
class IPResponse(IPSchema):
    id: Optional[int]
    """status: str"""
    affect_id: int
    ports: List[PortResponse]

    class Config:
        from_attributes = True
