from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class DeleteKeys(BaseModel):
    user_id: int
    server_key_if: Optional[str]
    protocol: str
    vless_uuid: Optional[UUID]

    model_config=ConfigDict(from_attributes=True)

class AccessUrlUser(BaseModel):
    access_url: str
    protocol: str

    model_config=ConfigDict(from_attributes=True)

class ReturnKeyForBot(BaseModel):
    access_url: str
    protocol: str

class CreateKeyApiBody(BaseModel):
    protocol:str