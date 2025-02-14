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

supported_device_lesson = Table(
    'supported_device_lesson',
    db.Model.metadata,
    db.Column('supported_device_id', db.Integer, db.ForeignKey('supported_device.id'), primary_key=True),
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True)
)

supported_device_simulation = Table(
    'supported_device_simulation',
    db.Model.metadata,
    db.Column('supported_device_id', db.Integer, db.ForeignKey('supported_device.id'), primary_key=True),
    db.Column('simulation_id', db.Integer, db.ForeignKey('simulation.id'), primary_key=True)
)

lesson_category_association = Table(
    'lesson_category_association',
    db.Model.metadata,
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('lesson_category.id'), primary_key=True)
)

device_category_association = Table(
    'device_category_association',
    db.Model.metadata,
    db.Column('device_id', db.Integer, db.ForeignKey('device.id'), primary_key=True),
    db.Column('device_category_id', db.Integer, db.ForeignKey('device_category.id'), primary_key=True)
)

simulation_category_association = Table(
    'simulation_category_association',
    db.Model.metadata,
    db.Column('simulation_id', db.Integer, db.ForeignKey('simulation.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('simulation_category.id'), primary_key=True)
)

simulation_device_category_association = Table(
    'simulation_device_category_association',
    db.Model.metadata,
    db.Column('simulation_id', db.Integer, db.ForeignKey('simulation.id'), primary_key=True),
    db.Column('device_category_id', db.Integer, db.ForeignKey('device_category.id'), primary_key=True)
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
    cover_image_url: Mapped[str] = mapped_column(db.String(2083), nullable=True)
    long_description: Mapped[str] = mapped_column(db.Text, nullable=True)
    learning_goals: Mapped[str] = mapped_column(db.Text, nullable=True)
    level: Mapped[str] = mapped_column(db.String(50), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    videos: Mapped[List['LessonVideo']] = \
        relationship("LessonVideo", back_populates="lesson", cascade="all, delete-orphan")
    images: Mapped[List['LessonImage']] = \
        relationship("LessonImage", back_populates="lesson", cascade="all, delete-orphan")
    lesson_documents: Mapped[List['LessonDoc']] = \
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
    lesson_categories: Mapped[List['LessonCategory']] = relationship(
        secondary=lesson_category_association,
        back_populates="lessons"
    )
    supported_devices: Mapped[List['SupportedDevice']] = relationship(
        secondary=supported_device_lesson,
        back_populates="lessons"
    )

class LessonVideo(db.Model):
    __tablename__ = 'lesson_video'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    video_url: Mapped[str] = mapped_column(db.String(2083), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="videos")

class LessonImage(db.Model):
    __tablename__ = 'lesson_image'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    image_url: Mapped[str] = mapped_column(db.String(2083), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="images")

class LessonDoc(db.Model):
    __tablename__ = 'lesson_doc'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    doc_url: Mapped[str] = mapped_column(db.String(2083), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    is_solution: Mapped[bool] = mapped_column(db.Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    lesson: Mapped['Lesson'] = relationship("Lesson", back_populates="lesson_documents")

class Device(db.Model):
    __tablename__ = 'device'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    description: Mapped[str] = mapped_column(db.Text)
    cover_image_url: Mapped[str] = mapped_column(db.String(2083), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    device_documents: Mapped[List['DeviceDoc']] = relationship("DeviceDoc", back_populates="device", cascade="all, delete-orphan")
    lessons: Mapped[List['Lesson']] = relationship(
        secondary=lesson_device_association,
        back_populates="devices"
    )
    simulations: Mapped[List['Simulation']] = relationship(
        secondary=device_simulation_association,
        back_populates="devices"
    )
    device_categories: Mapped[List['DeviceCategory']] = relationship(
        secondary=device_category_association,
        back_populates="devices"
    )

class DeviceDoc(db.Model):
    __tablename__ = 'device_doc'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    doc_url: Mapped[str] = mapped_column(db.String(2083), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    device: Mapped['Device'] = relationship("Device", back_populates="device_documents")

class Simulation(db.Model):
    __tablename__ = 'simulation'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    slug: Mapped[str] = mapped_column(db.String(100), unique=True)
    description: Mapped[str] = mapped_column(db.Text)
    cover_image_url: Mapped[str] = mapped_column(db.String(2083), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(db.DateTime, server_default=func.now(), onupdate=func.now())

    simulation_documents: Mapped[List['SimulationDoc']] = relationship(
        back_populates="simulation", cascade="all, delete-orphan"
    )
    lessons: Mapped[List['Lesson']] = relationship(
        secondary=lesson_simulation_association,
        back_populates="simulations"
    )
    devices: Mapped[List['Device']] = relationship(
        secondary=device_simulation_association,
        back_populates="simulations"
    )
    supported_devices: Mapped[List['SupportedDevice']] = relationship(
        secondary=supported_device_simulation,
        back_populates="simulations"
    )
    simulation_categories: Mapped[List['SimulationCategory']] = relationship(
        secondary=simulation_category_association,
        back_populates="simulations"
    )
    simulation_device_categories: Mapped[List['DeviceCategory']] = relationship(
        secondary=simulation_device_category_association,
        back_populates="simulations"
    )

class SimulationDoc(db.Model):
    __tablename__ = 'simulation_doc'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('simulation.id'), nullable=False)
    doc_url: Mapped[str] = mapped_column(db.String(2083), nullable=False)
    title: Mapped[str] = mapped_column(db.String(100), nullable=True)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    simulation: Mapped['Simulation'] = relationship("Simulation", back_populates="simulation_documents")


class SupportedDevice(db.Model):
    __tablename__ = 'supported_device'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    slug: Mapped[str] = mapped_column(db.String(100), unique=True)
    cover_image_url: Mapped[str] = mapped_column(db.String(2083), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(db.DateTime, server_default=func.now(), onupdate=func.now())

    lessons: Mapped[List['Lesson']] = relationship(
        secondary=supported_device_lesson,
        back_populates="supported_devices"
    )
    simulations: Mapped[List['Simulation']] = relationship(
        secondary=supported_device_simulation,
        back_populates="supported_devices"
    )

class LessonCategory(db.Model):
    __tablename__ = 'lesson_category'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(db.DateTime, server_default=func.now(), onupdate=func.now())

    lessons: Mapped[List['Lesson']] = relationship(
        secondary=lesson_category_association,
        back_populates="lesson_categories"
    )

    def __str__(self):
        return self.name

class DeviceCategory(db.Model):
    __tablename__ = 'device_category'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)
    slug: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(db.DateTime, server_default=func.now(), onupdate=func.now())

    devices: Mapped[List['Device']] = relationship(
        secondary=device_category_association,
        back_populates="device_categories"
    )
    simulations: Mapped[List['Simulation']] = relationship(
        secondary=simulation_device_category_association,
        back_populates="simulation_device_categories"
    )

    def __str__(self):
        return self.name

class SimulationCategory(db.Model):
    __tablename__ = 'simulation_category'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(db.DateTime, server_default=func.now(), onupdate=func.now())

    simulations: Mapped[List['Simulation']] = relationship(
        secondary="simulation_category_association",
        back_populates="simulation_categories"
    )

    def __str__(self):
        return self.name
