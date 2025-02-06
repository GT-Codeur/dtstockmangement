from typing import Annotated, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Header, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import Item, User
from sqlmodel import create_engine, SQLModel, Session, select
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from datetime import datetime

app = FastAPI()

# Mounting the static files
app.mount('/static', StaticFiles(directory='static'), name='static')

# HTML template for the frontend
templates = Jinja2Templates(directory='templates')

# database setup
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, connect_args={"timeout": 20, "check_same_thread": False})
SQLModel.metadata.create_all(engine)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

# Global variables
load_dotenv()
secret_key = os.getenv('SECRET_KEY')
algo = os.getenv('ALGORITHM')


def get_session():
    with Session(engine) as session:
        yield session


def read_items(
        session: Annotated[Session, Depends(get_session)], skip: int = 0, limit: int = 10
):
    items = session.exec(select(Item).offset(skip).limit(limit)).all()
    if not items:
        raise HTTPException(status_code=404, detail="No item found.")
    return items


# Route in case of error
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html",
                                      {"request": request, "status_code": exc.status_code, "detail": exc.detail})


# Root of the app
@app.get('/')
async def home(request: Request, session: Annotated[Session, Depends(get_session)]) -> HTMLResponse:
    items = read_items(session)
    return templates.TemplateResponse(request, './index.html', context={'items': items})


# Login page of the app for any administration
@app.post('/login')
async def login():
    return RedirectResponse(url='./login.html')


@app.get('/login')
async def login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name='./login.html', context={})


# Items endpoints
@app.post('/create_item')
def create_item(item: Item, session: Annotated[Session, Depends(get_session)]):
    item.last_modification = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# User endpoints
@app.post('/create_user')
def create_user(user: User, session: Annotated[Session, Depends(get_session)]):
    user.password = pwd_context.hash(user.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post('/signin')
def get_user(username: Annotated[str, Form()],
             password: Annotated[str, Form()],
             request: Request, session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return templates.TemplateResponse(
            request, "./login.html", context={"incorrect": True}
        )
    if not pwd_context.verify(password, user.password):
        return templates.TemplateResponse(
            request, "./login.html", context={"incorrect": True}
        )
    items = read_items(session)
    return templates.TemplateResponse(
        request, "./index_admin.html", context={"username": username, 'items': items}
    )


# Edit an item
@app.get('/item/{item_id}')
async def edit_item(item_id: int, request: Request, session: Annotated[Session, Depends(get_session)]):
    items = read_items(session)
    item = session.exec(select(Item).where(Item.id == item_id)).first()
    return templates.TemplateResponse(
        request, "./edit_item.html", context={'item': item, 'items': items}
    )


@app.post('/item/{item_id}')
async def edit_item():
    return RedirectResponse(url="./edit_item.html")


@app.put('/update_item/{item_id}')
async def update_item(item_id: int, qty: Annotated[int, Form()], request: Request,
                      session: Annotated[Session, Depends(get_session)], hx_request: Optional[str] = Header(None)):
    item = session.exec(select(Item).where(Item.id == item_id)).one()
    item.quantity = qty
    session.add(item)
    session.commit()
    session.refresh(item)
    items = read_items(session)
    if hx_request:
        return templates.TemplateResponse(
            request, "./item_edited.html", context={'item': item, 'items': items}
        )
    return templates.TemplateResponse(
        request, "./edit_item.html", context={'item': item, 'items': items}
    )


@app.delete('/delete_item/{item_id}')
async def delete_item(item_id: int, request: Request,
                      session: Annotated[Session, Depends(get_session)]):
    item = session.exec(select(Item).where(Item.id == item_id)).one()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return templates.TemplateResponse(
        request, "./index_admin.html", context={'items': read_items(session)}
    )


@app.post('/create_item')
async def add_item(item: Item, session: Annotated[Session, Depends(get_session)],):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
