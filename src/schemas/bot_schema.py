from pydantic import BaseModel, ConfigDict

class UserRegister(BaseModel):
    user_id: int
    username:str | None
    first_name:str
    referrer_id:int | None


class UserUpdateBalance(BaseModel):
    amount:int

class CheckUserBalance(BaseModel):
    balance: int

    model_config = ConfigDict(from_attributes=True)

