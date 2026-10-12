# src/database/connection.py
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import (
    Base,
    Course,
    ScheduleBlock,
    Assignment,
    DegreeRequirement,
    StudentProfile,
    Contact,
)

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


def _migrate_schema(engine_instance) -> None:
    """Performs schema migrations for newly added model columns and tables."""
    with engine_instance.connect() as conn:
        # Check student_profile table columns
        cursor = conn.exec_driver_sql("PRAGMA table_info(student_profile)")
        profile_cols = [row[1] for row in cursor.fetchall()]
        if profile_cols:
            if "total_credits_required" not in profile_cols:
                conn.exec_driver_sql("ALTER TABLE student_profile ADD COLUMN total_credits_required INTEGER DEFAULT 120")
            if "degree_contract_path" not in profile_cols:
                conn.exec_driver_sql("ALTER TABLE student_profile ADD COLUMN degree_contract_path VARCHAR(500)")

        # Check assignments table columns
        cursor_asgn = conn.exec_driver_sql("PRAGMA table_info(assignments)")
        asgn_cols = [row[1] for row in cursor_asgn.fetchall()]
        if asgn_cols:
            if "notes" not in asgn_cols:
                conn.exec_driver_sql("ALTER TABLE assignments ADD COLUMN notes VARCHAR(500)")
            if "submission_link" not in asgn_cols:
                conn.exec_driver_sql("ALTER TABLE assignments ADD COLUMN submission_link VARCHAR(255)")

        conn.commit()


def init_db() -> None:
    """Creates database tables, applies migrations, and populates seed data if empty."""
    Base.metadata.create_all(bind=engine)
    _migrate_schema(engine)

    with get_db_session() as db:
        if db.query(StudentProfile).count() == 0:
            default_profile = StudentProfile(
                name="Alex Johnson",
                student_id_number="STU-98214",
                major="Computer Science B.S.",
                email="alex.johnson@university.edu",
                total_credits_required=120,
                degree_contract_path=None,
            )
            db.add(default_profile)

        if db.query(Contact).count() == 0:
            seed_contacts = [
                Contact(
                    name="Dr. Alan Turing",
                    email="a.turing@university.edu",
                    phone="(555) 019-2831",
                    address="Science Hall, Office 304",
                    links="https://university.edu/faculty/turing",
                    notes="CS101 Professor. Office hours on Mon/Wed 2-4 PM.",
                    image_path=None,
                ),
                Contact(
                    name="Academic Advising Center",
                    email="advising@university.edu",
                    phone="(555) 012-3456",
                    address="Student Union, Room 210",
                    links="https://university.edu/advising",
                    notes="Main contact for degree evaluation and course overrides.",
                    image_path=None,
                ),
                Contact(
                    name="Financial Aid Office",
                    email="finaid@university.edu",
                    phone="(555) 014-9876",
                    address="Administration Bldg, 1st Floor",
                    links="https://university.edu/finaid",
                    notes="FAFSA submission deadlines and scholarship info.",
                    image_path=None,
                ),
            ]
            db.add_all(seed_contacts)

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
                    notes="Complete stack and queue implementations in Python.",
                    submission_link="https://canvas.university.edu",
                ),
                Assignment(
                    title="Integration by Parts Worksheet",
                    course_id=math201.id,
                    due_date="2026-10-15",
                    status="Pending",
                    priority="Medium",
                    notes="Submit odd-numbered exercises 1-25.",
                    submission_link=None,
                ),
                Assignment(
                    title="Kinematics Lab Report",
                    course_id=phys101.id,
                    due_date="2026-10-22",
                    status="Pending",
                    priority="High",
                    notes="Include error analysis and scatter plots.",
                    submission_link="https://canvas.university.edu",
                ),
                Assignment(
                    title="Argumentative Essay First Draft",
                    course_id=eng102.id,
                    due_date="2026-10-12",
                    status="Done",
                    priority="Low",
                    notes="Peer review completed in class.",
                    submission_link=None,
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
