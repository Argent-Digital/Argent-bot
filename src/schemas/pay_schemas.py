
from pydantic import BaseModel, ConfigDict


class SuccesPay(BaseModel):
    amount: int

class UserWithLowBalance(BaseModel):
    user_id: int

    model_config=ConfigDict(from_attributes=True)

class BillingResponse(BaseModel):
    deleted_keys: list[int]
    user_lower: list[int]

class CreatePaymentUrl(BaseModel):
    amount: int

class ReturnUrl(BaseModel):
    url: str
