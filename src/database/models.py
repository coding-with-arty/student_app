# src/database/models.py
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    professor: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#2196F3")
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Relational mappings
    schedule_blocks: Mapped[List["ScheduleBlock"]] = relationship(
        "ScheduleBlock", back_populates="course", cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="course", cascade="all, delete-orphan"
    )


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    room: Mapped[str] = mapped_column(String(50), nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="schedule_blocks")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    due_date: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pending")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submission_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")


class DegreeRequirement(Base):
    __tablename__ = "degree_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    prerequisite_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Planned")


class StudentProfile(Base):
    __tablename__ = "student_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Alex Johnson")
    student_id_number: Mapped[str] = mapped_column(String(50), nullable=False, default="STU-98214")
    major: Mapped[str] = mapped_column(String(100), nullable=False, default="Computer Science B.S.")
    email: Mapped[str] = mapped_column(String(100), nullable=False, default="alex.johnson@university.edu")
    total_credits_required: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    degree_contract_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    links: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
