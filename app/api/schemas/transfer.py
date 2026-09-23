from pydantic import BaseModel,Field
from decimal import Decimal

class Transfer(BaseModel):
    name:str
    amount:Decimal = Field(gt=0)


    