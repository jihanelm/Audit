from pydantic import BaseModel
from typing import Optional

class PortSchema(BaseModel):
    port: int
    status: Optional[str] = "open"

class PortResponse(PortSchema):
    id: int

    class Config:
        from_attributes = True
