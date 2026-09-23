import uvicorn
from fastapi import FastAPI,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from app.api.endpoints.todo import todo_router
from app.db.database import db
from app.security.utils import verify_password,hash_password,registration
from app.security.dependencies import decode_token,encode_token,get_access,get_roles,get_user
from app.api.schemas.security import User_login,User_db
from app.api.endpoints.transfer import transfer_router
from app.cache.redis import cache

from app.llm.client import ask_llm


@asynccontextmanager
async def lifespan(app:FastAPI):
    global cache
    await db.connect()

    yield
    await cache.redis.close()
    await db.disconnect()



app = FastAPI(lifespan=lifespan)

app.include_router(todo_router)
app.include_router(transfer_router)

@app.post("/register")
async def register(user:User_login):
    await registration(user.username,user.password)
    return {"detail":"New user has been created"}

@app.post("/login")
async def login(user:OAuth2PasswordRequestForm = Depends()):
    a = await db.fetch("select username,password from users join users_roles using(user_Id) join roles using(role_id) where username = $1",user.username)
    if not a:
        raise HTTPException(status_code=401, detail="Wrong password")
    credents = User_db(username = a[0]["username"],hashed_password = a[0]["password"])
    if verify_password(user.password,credents.hashed_password):
        token = encode_token({"sub":user.username,"type":"Access"})
    else:
        raise HTTPException(status_code=401, detail="Wrong password")
    return {"access_token": token, "token_type": "bearer"}

@app.get("/info")
async def get_info(payload:str = Depends(get_access)):
    return{"Username":payload["sub"],"Roles":await get_roles(payload["sub"])}

@app.post("/chat")
async def llm_chat(q:str):
    return await ask_llm(q)
    
    
    








if __name__ == "__main__":
    uvicorn.run(app="main:app",reload =True)