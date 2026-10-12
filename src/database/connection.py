# src/database/connection.py
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Course, ScheduleBlock, Assignment, DegreeRequirement, StudentProfile

DB_FILENAME = "student_app.db"
DATABASE_URL = f"sqlite:///{DB_FILENAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provides a transactional scope around database operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Creates database tables and populates seed data if empty."""
    Base.metadata.create_all(bind=engine)

    with get_db_session() as db:
        if db.query(StudentProfile).count() == 0:
            default_profile = StudentProfile(
                name="Alex Johnson",
                student_id_number="STU-98214",
                major="Computer Science B.S.",
                email="alex.johnson@university.edu",
            )
            db.add(default_profile)

        if db.query(Course).count() == 0:
            cs101 = Course(
                title="Introduction to Computer Science",
                code="CS101",
                professor="Dr. Alan Turing",
                color="#1E88E5",
                credits=4,
            )
            math201 = Course(
                title="Calculus II",
                code="MATH201",
                professor="Dr. Katherine Johnson",
                color="#43A047",
                credits=3,
            )
            phys101 = Course(
                title="General Physics I",
                code="PHYS101",
                professor="Dr. Richard Feynman",
                color="#E53935",
                credits=4,
            )
            eng102 = Course(
                title="Academic Writing",
                code="ENG102",
                professor="Dr. Maya Angelou",
                color="#FB8C00",
                credits=3,
            )

            db.add_all([cs101, math201, phys101, eng102])
            db.flush()

            blocks = [
                ScheduleBlock(
                    course_id=cs101.id,
                    day_of_week="Monday",
                    start_time="09:00",
                    end_time="10:30",
                    room="Science Hall 101",
                ),
                ScheduleBlock(
                    course_id=cs101.id,
                    day_of_week="Wednesday",
                    start_time="09:00",
                    end_time="10:30",
                    room="Science Hall 101",
                ),
                ScheduleBlock(
                    course_id=math201.id,
                    day_of_week="Tuesday",
                    start_time="11:00",
                    end_time="12:30",
                    room="Math Building 204",
                ),
                ScheduleBlock(
                    course_id=math201.id,
                    day_of_week="Thursday",
                    start_time="11:00",
                    end_time="12:30",
                    room="Math Building 204",
                ),
                ScheduleBlock(
                    course_id=phys101.id,
                    day_of_week="Monday",
                    start_time="13:00",
                    end_time="14:30",
                    room="Physics Lab 3",
                ),
                ScheduleBlock(
                    course_id=eng102.id,
                    day_of_week="Friday",
                    start_time="10:00",
                    end_time="11:30",
                    room="Humanities 105",
                ),
            ]
            db.add_all(blocks)

            assignments = [
                Assignment(
                    title="Python Data Structures Lab",
                    course_id=cs101.id,
                    due_date="2026-10-18",
                    status="In-Progress",
                    priority="High",
                ),
                Assignment(
                    title="Integration by Parts Worksheet",
                    course_id=math201.id,
                    due_date="2026-10-15",
                    status="Pending",
                    priority="Medium",
                ),
                Assignment(
                    title="Kinematics Lab Report",
                    course_id=phys101.id,
                    due_date="2026-10-22",
                    status="Pending",
                    priority="High",
                ),
                Assignment(
                    title="Argumentative Essay First Draft",
                    course_id=eng102.id,
                    due_date="2026-10-12",
                    status="Done",
                    priority="Low",
                ),
            ]
            db.add_all(assignments)

            requirements = [
                DegreeRequirement(course_code="CS101", prerequisite_code=None, status="Completed"),
                DegreeRequirement(course_code="MATH201", prerequisite_code="MATH101", status="Completed"),
                DegreeRequirement(course_code="CS102", prerequisite_code="CS101", status="Planned"),
                DegreeRequirement(course_code="CS201", prerequisite_code="CS102", status="Planned"),
                DegreeRequirement(course_code="PHYS101", prerequisite_code=None, status="Completed"),
            ]
            db.add_all(requirements)
