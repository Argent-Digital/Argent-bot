from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeleteKeys(BaseModel):
    user_id: int
    server_key_if: str | None
    protocol: str
    vless_uuid: UUID | None

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
