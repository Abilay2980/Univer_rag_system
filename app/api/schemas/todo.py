from pydantic import BaseModel
from datetime import datetime
class Todo(BaseModel):
    name:str
    description:str
    completed:bool

