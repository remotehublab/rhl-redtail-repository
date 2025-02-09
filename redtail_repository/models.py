from typing import List

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Table
from sqlalchemy.sql import func
from datetime import datetime

from redtail_repository import db

# Association Tables
author_lesson_association = Table(
    'author_lesson',
    db.Model.metadata,
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True),
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True)
)

lesson_device_association = Table(
    'lesson_device',
    db.Model.metadata,
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True),
    db.Column('device_id', db.Integer, db.ForeignKey('device.id'), primary_key=True)
)

lesson_simulation_association = Table(
    'lesson_simulation',
    db.Model.metadata,
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True),
    db.Column('simulation_id', db.Integer, db.ForeignKey('simulation.id'), primary_key=True)
)

device_simulation_association = Table(
    'device_simulation',
    db.Model.metadata,
    db.Column('device_id', db.Integer, db.ForeignKey('device.id'), primary_key=True),
    db.Column('simulation_id', db.Integer, db.ForeignKey('simulation.id'), primary_key=True)
)

class Author(db.Model):
    __tablename__ = 'author'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    link: Mapped[str] = mapped_column(db.String(255))

    users: Mapped['User'] = relationship("User", back_populates="author")
    lessons: Mapped[List['Lesson']] = relationship(
        secondary=author_lesson_association,
        back_populates="authors"
    )

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    login: Mapped[str] = mapped_column(db.String(100), unique=True)
    name: Mapped[str] = mapped_column(db.String(255))
    author_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("author.id"), nullable=True)

    password_hash: Mapped[str] = mapped_column(db.String(255))

    # Must be 'admin', 'instructor'
    role: Mapped[str] = mapped_column(db.String(100))

    verified: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # Many-to-one relationship
    author: Mapped[Author] = relationship("Author", back_populates="users")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Lesson(db.Model):
    __tablename__ = 'lesson'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    slug: Mapped[str] = mapped_column(db.String(255), unique=True)
    short_description: Mapped[str] = mapped_column(db.String(255))
    active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson_category.id'), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    videos: Mapped[List['LessonVideo']] = \
        relationship("LessonVideo", back_populates="lesson", cascade="all, delete-orphan")
    images: Mapped[List['LessonImage']] = \
        relationship("LessonImage", back_populates="lesson", cascade="all, delete-orphan")
    documents: Mapped[List['LessonDoc']] = \
        relationship("LessonDoc", back_populates="lesson", cascade="all, delete-orphan")

    authors: Mapped[List['Author']] = relationship(
        secondary=author_lesson_association,
        back_populates="lessons"
    )
    devices: Mapped[List['Device']] = relationship(
        secondary=lesson_device_association,
        back_populates="lessons"
    )
    simulations: Mapped[List['Simulation']] = relationship(
        secondary=lesson_simulation_association,
        back_populates="lessons"
    )
    category: Mapped['LessonCategory'] = relationship(
        back_populates="lessons")

class LessonVideo(db.Model):
    __tablename__ = 'lesson_video'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    video_url: Mapped[str] = mapped_column(db.String(255), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="videos")

class LessonImage(db.Model):
    __tablename__ = 'lesson_image'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    image_url: Mapped[str] = mapped_column(db.String(255), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="images")

class LessonDoc(db.Model):
    __tablename__ = 'lesson_doc'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    doc_url: Mapped[str] = mapped_column(db.String(255), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="documents")

class LessonCategory(db.Model):
    __tablename__ = 'lesson_category'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)

    lessons: Mapped[List['Lesson']] = relationship("Lesson", back_populates="category")

    def __str__(self):
        return self.name

class Device(db.Model):
    __tablename__ = 'device'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    description: Mapped[str] = mapped_column(db.Text)

    lessons: Mapped[List['Lesson']] = relationship(
        secondary=lesson_device_association,
        back_populates="devices"
    )
    simulations: Mapped[List['Simulation']] = relationship(
        secondary=device_simulation_association,
        back_populates="devices"
    )

class Simulation(db.Model):
    __tablename__ = 'simulation'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    description: Mapped[str] = mapped_column(db.Text)

    lessons: Mapped[List['Lesson']] = relationship(
        secondary=lesson_simulation_association,
        back_populates="simulations"
    )
    devices: Mapped[List['Device']] = relationship(
        secondary=device_simulation_association,
        back_populates="simulations"
    )