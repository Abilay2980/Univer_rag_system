from pydantic import BaseModel
class User_login(BaseModel):
    username:str
    password:str

class User_db(BaseModel):
    username:str
    hashed_password:str