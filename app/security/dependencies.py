from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException,Depends
from functools import wraps
from datetime import datetime,timedelta
from app.core.config import settings
import jwt
from app.db.database import db


oauth = OAuth2PasswordBearer("/login")
secret_word = settings.SECRET_WORD
algorithm="HS256"
access_token_time = 15 #minutes
refresh_token_time = 2 #days

def encode_token(data:dict):
    to_encode = data.copy()
    if data["type"] not in ["Access","Refresh"]:
        raise HTTPException(status_code=401,detail="Theres no such type of token")
    elif data["type"] == "Access":
        exp = datetime.utcnow()+timedelta(minutes=access_token_time)
    else:
        exp = datetime.utcnow()+timedelta(days = refresh_token_time)
    to_encode.update({"exp":exp})
    token = jwt.encode(to_encode,key=secret_word,algorithm=algorithm)
    return token
    
def decode_token(to_decode:str):
    try:
        payload = jwt.decode(to_decode,key = secret_word, algorithms=[algorithm])
        return payload
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=500,detail="expired signarute")
    raise HTTPException(status_code=400,detail="damaged token")
    
    
async def get_roles(sub:str):
    res = await db.fetch("select role from users join users_roles using(user_Id) join roles using(role_id) where username = $1",sub)
    res = [i["role"] for i in res]
    return res
        


def get_access(token = Depends(oauth)):
    payload = decode_token(token)
    return payload

async def get_user(payload : str = Depends(get_access)):
    res = await db.fetch("select username,password from users join users_roles using(user_Id) join roles using(role_id) where username = $1",payload["sub"])
    return User_db(username=res["username"],hash_password=res["password"])

class Permission_Checker():
    def __init__(self,roles:list[str]):
        self.roles = roles

    def __call__(self,func):
        @wraps(func)
        async def wrapper(*args,**kwargs):
            user = kwargs.get("payload")
            if not user:
                raise HTTPException(status_code=403,detail="Error)")
            user_roles = await get_roles(user.get("sub"))
            if not set(user_roles)&set(self.roles):
                raise HTTPException(status_code=403,detail="No access")
            return await func(*args,**kwargs)
        return wrapper
        
            



        
