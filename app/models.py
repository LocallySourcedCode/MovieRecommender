from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional

class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("email"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    password_hash: str
