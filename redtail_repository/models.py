from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship

from redtail_repository import db

class Author(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    link: Mapped[str] = mapped_column(db.String(255))

class User(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    author_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("author.id"))

    # Many-to-one relationship
    # author: Mapped[Author] = relationship("Author", back_populates="users")


class Lesson(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    short_description: Mapped[str] = mapped_column(db.String(255))

