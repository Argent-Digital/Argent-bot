from pydantic import BaseModel

class SuccesPay(BaseModel):
    user_id: int
    amount: int