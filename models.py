from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from datetime import datetime
import re


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    email: EmailStr = None
    username: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=8, regex=r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_]).*$")
    is_superuser: bool = None
    is_active: bool = None


class Item(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    description: str
    quantity: int
    unit_price: Optional[int] = None
    last_modification: datetime = None
