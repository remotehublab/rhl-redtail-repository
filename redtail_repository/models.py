from typing import List

from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import Mapped, mapped_column, relationship

from redtail_repository import db

class Author(db.Model):

    __tablename__ = 'author'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    link: Mapped[str] = mapped_column(db.String(255))

    users: Mapped['User'] = relationship("User", back_populates="author")

class User(db.Model):

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    author_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("author.id"))

    password_hash: Mapped[str] = mapped_column(db.String(255))

    # Many-to-one relationship
    author: Mapped[Author] = relationship("Author", back_populates="users")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Lesson(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    short_description: Mapped[str] = mapped_column(db.String(255))

