from passlib.context import CryptContext
from app.security.dependencies import get_access
from fastapi import Depends ,HTTPException
from app.api.schemas.security import User_db
from bs4 import BeautifulSoup
import requests
from decimal import Decimal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(password:str, hashed_password:str):
    return pwd_context.verify(password, hashed_password)

from app.db.database import db


async def ex_rate():
    url = "https://www.mig.kz/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    allNews = soup.find_all("td")
    allNews = [i.text for i in allNews if len(i.text.strip())>2 and i.text != "по курсу"]
    new = []
    for i in range(0,len(allNews),3):
        new.append({"currency":allNews[i+1],"sell":Decimal(allNews[i]),"buy":Decimal(allNews[i+2])})
    return new


async def get_id_by_sub(sub:str):
    res = await db.fetch("select user_id from users where username = $1",sub)
    return res[0]["user_id"]


async def registration(name:str,password:str):
    async with db.transaction(isolation='serializable'):
        a = await db.fetch("select username from users join users_roles using(user_Id) join roles using(role_id) where username = $1",name)
        if a:
            raise HTTPException(status_code=401,detail="This name is already taken")
        hashed_pass = hash_password(password)
        await db.execute("insert into users(username,password) values($1,$2)",name,hashed_pass)
        await db.execute("insert into users_roles(user_id,role_id) values($1,(select role_id from roles where role = 'user'))",await get_id_by_sub(name))
        await db.execute("insert into users_balances(user_id,balance,currency) values($1,$2,'KZT')",await get_id_by_sub(name),Decimal(0))

async def transfer_money(sender:str,receiver:str,amount:Decimal):
    async with db.transaction(isolation='serializable'):
        try:
            if sender == receiver:
                raise HTTPException(status_code=400,detail="Bad request1")
            res = await db.fetch("select balance from users join users_balances using(user_id) where username = $1",sender)
            if res[0]["balance"] < amount:
                raise HTTPException(status_code=400,detail="Not enough funds")
            await db.execute("insert into transactions(from_id,to_id,amount,currency) values($1,$2,$3,$4)",await get_id_by_sub(sender),await get_id_by_sub(receiver),amount,"KZT")
            res = await db.fetch("update users_balances set balance= balance -$1 where user_id = (select user_id from users where username = $2) returning balance",amount,sender)
            await db.execute("update users_balances set balance=balance+$1 where user_id = (select user_id from users where username = $2)",amount,receiver)
            return{"detail":"success","balance":res}
        except Exception as e:
            raise HTTPException(status_code=400)

async def change_balance(sender,receiver:str,amount:Decimal):
    async with db.transaction(isolation='serializable'):
        try:
            bal = await db.fetch("update users_balances set balance = $1 where user_id = (select user_id from  users where username = $2) returning balance",amount,receiver)
            await db.execute("insert into transactions(from_id,to_id,amount,currency,type) values($1,$2,$3,$4,$5)",await get_id_by_sub(sender),await get_id_by_sub(receiver),amount,"KZT",'admin_edit')
            return{"detail":"success","balance":bal[0]["balance"]}
        except Exception as e:
            return{"detail":str(e)}
            raise HTTPException(status_code=400,detail="Bad Request3")


    

        

        





