from pydantic import BaseModel, EmailStr

class MerchantCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class MerchantLogin(BaseModel):
    email: EmailStr
    password: str

class OrderCreate(BaseModel):
    amount: float
    currency: str = "INR"
    merchant_api_key: str


class OrderOut(BaseModel):
    id: int
    amount: float
    currency: str
    status: str

    class Config:
        orm_mode = True
