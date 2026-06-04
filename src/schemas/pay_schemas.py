from pydantic import BaseModel, ConfigDict

class SuccesPay(BaseModel):
    amount: int

class UserWithLowBalance(BaseModel):
    user_id: int

    model_config=ConfigDict(from_attributes=True)