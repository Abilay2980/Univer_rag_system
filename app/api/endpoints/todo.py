from fastapi import APIRouter
from app.db.database import db
from app.api.schemas.todo import Todo

todo_router = APIRouter(
    prefix="/todo",
    tags=["ToDo"]
)

@todo_router.post("/create_table")
async def create_todo():
    await db.execute("create table if not exists todo(name varchar(20),description varchar(150),completed bool)")
    return {"status":200}

@todo_router.get("/")
async def get_todos():
    res = await db.fetch("select * from todo ")
    return{"detail":res}
    pass


@todo_router.post("/")
async def create_in_todo(ex:Todo):
    await db.fetch("insert into todo(name,description,completed) values($1,$2,$3)",ex.name,ex.description,ex.completed)
    return {"detail":"Success"}
