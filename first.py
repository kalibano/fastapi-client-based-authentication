from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, Item

app = FastAPI()


class ItemCreate(BaseModel):
    id: int | None = None
    title: str | None = None
    description: str | None = None


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


@app.post("/saveItem")
def save_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/list")
def list_of_items(db: Session = Depends(get_db)):
    db_item = db.query(Item).all()
    return db_item


@app.post("/getItem")
def get_item(item: ItemCreate, db: Session = Depends(get_db)):
    try:
        db_item = db.query(Item).filter(Item.id == item.id).first()
        return db_item
    except Exception as e:
        print(e)


@app.post("/deleteItem")
def delete_item():
    return {}
