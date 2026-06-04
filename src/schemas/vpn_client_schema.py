from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID

class DeleteKeys(BaseModel):
    user_id: int
    server_key_if: Optional[str]
    protocol: str
    vless_uuid: Optional[UUID]

    model_config=ConfigDict(from_attributes=True)

class BillingResponse(BaseModel):
    deleted_keys: List[int]
    user_lower: List[int]