# src/database/crud.py
from typing import List, Optional
from sqlalchemy.orm import joinedload
from database.connection import get_db_session
from database.models import Course, ScheduleBlock, Assignment, DegreeRequirement, StudentProfile, Contact


# --- Student Profile Operations ---
def get_student_profile() -> Optional[StudentProfile]:
    with get_db_session() as db:
        return db.query(StudentProfile).first()


def update_student_profile(
    name: str, student_id_number: str, major: str, email: str
) -> StudentProfile:
    with get_db_session() as db:
        profile = db.query(StudentProfile).first()
        if not profile:
            profile = StudentProfile(
                name=name,
                student_id_number=student_id_number,
                major=major,
                email=email,
            )
            db.add(profile)
        else:
            profile.name = name
            profile.student_id_number = student_id_number
            profile.major = major
            profile.email = email
        db.flush()
        db.refresh(profile)
        return profile


def update_degree_settings(
    total_credits: int, contract_path: Optional[str] = None
) -> StudentProfile:
    with get_db_session() as db:
        profile = db.query(StudentProfile).first()
        if not profile:
            profile = StudentProfile(
                name="Alex Johnson",
                student_id_number="STU-98214",
                major="Computer Science B.S.",
                email="alex.johnson@university.edu",
                total_credits_required=total_credits,
                degree_contract_path=contract_path,
            )
            db.add(profile)
        else:
            profile.total_credits_required = total_credits
            if contract_path is not None:
                profile.degree_contract_path = contract_path
        db.flush()
        db.refresh(profile)
        return profile


# --- Contact Operations ---
def get_contacts() -> List[Contact]:
    """Retrieves all contacts sorted alphabetically by name."""
    with get_db_session() as db:
        return db.query(Contact).order_by(Contact.name.asc()).all()


def get_contact(contact_id: int) -> Optional[Contact]:
    """Retrieves a single contact record by ID."""
    with get_db_session() as db:
        return db.query(Contact).filter(Contact.id == contact_id).first()


def create_contact(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    links: Optional[str] = None,
    notes: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Contact:
    """Creates a new contact in the address book."""
    with get_db_session() as db:
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            address=address,
            links=links,
            notes=notes,
            image_path=image_path,
        )
        db.add(contact)
        db.flush()
        db.refresh(contact)
        return contact


def update_contact(
    contact_id: int,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    links: Optional[str] = None,
    notes: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Optional[Contact]:
    """Updates an existing contact record."""
    with get_db_session() as db:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            contact.name = name
            contact.email = email
            contact.phone = phone
            contact.address = address
            contact.links = links
            contact.notes = notes
            contact.image_path = image_path
            db.flush()
            db.refresh(contact)
        return contact


def delete_contact(contact_id: int) -> bool:
    """Deletes a contact record by ID."""
    with get_db_session() as db:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            db.delete(contact)
            return True
        return False


# --- Course Operations ---
def get_or_create_course(code: str, title: str) -> Course:
    code_clean = code.strip().upper()
    title_clean = title.strip() or code_clean
    with get_db_session() as db:
        course = db.query(Course).filter(Course.code == code_clean).first()
        if not course:
            course = Course(
                title=title_clean,
                code=code_clean,
                professor="Staff",
                color="#2196F3",
                credits=3,
            )
            db.add(course)
            db.flush()
            db.refresh(course)
        elif title_clean and course.title != title_clean:
            course.title = title_clean
            db.flush()
            db.refresh(course)
        return course


def create_course(
    title: str, code: str, professor: str, color: str = "#2196F3", credits: int = 3
) -> Course:
    with get_db_session() as db:
        course = Course(
            title=title, code=code, professor=professor, color=color, credits=credits
        )
        db.add(course)
        db.flush()
        db.refresh(course)
        return course


def get_courses() -> List[Course]:
    with get_db_session() as db:
        return db.query(Course).all()


def delete_course(course_id: int) -> bool:
    with get_db_session() as db:
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            db.delete(course)
            return True
        return False


# --- ScheduleBlock Operations ---
def create_schedule_block(
    course_id: int, day_of_week: str, start_time: str, end_time: str, room: str
) -> ScheduleBlock:
    with get_db_session() as db:
        block = ScheduleBlock(
            course_id=course_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            room=room,
        )
        db.add(block)
        db.flush()
        db.refresh(block)
        return block


def create_schedule_block_by_code(
    course_code: str,
    course_title: str,
    day_of_week: str,
    start_time: str,
    end_time: str,
    room: str,
) -> ScheduleBlock:
    course = get_or_create_course(course_code, course_title)
    return create_schedule_block(
        course_id=course.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room,
    )


def get_schedule_blocks() -> List[ScheduleBlock]:
    with get_db_session() as db:
        return db.query(ScheduleBlock).options(joinedload(ScheduleBlock.course)).all()


def update_schedule_block(
    block_id: int, course_id: int, day_of_week: str, start_time: str, end_time: str, room: str
) -> Optional[ScheduleBlock]:
    with get_db_session() as db:
        block = db.query(ScheduleBlock).filter(ScheduleBlock.id == block_id).first()
        if block:
            block.course_id = course_id
            block.day_of_week = day_of_week
            block.start_time = start_time
            block.end_time = end_time
            block.room = room
            db.flush()
            db.refresh(block)
        return block


def update_schedule_block_by_code(
    block_id: int,
    course_code: str,
    course_title: str,
    day_of_week: str,
    start_time: str,
    end_time: str,
    room: str,
) -> Optional[ScheduleBlock]:
    course = get_or_create_course(course_code, course_title)
    return update_schedule_block(
        block_id=block_id,
        course_id=course.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room,
    )


def delete_schedule_block(block_id: int) -> bool:
    with get_db_session() as db:
        block = db.query(ScheduleBlock).filter(ScheduleBlock.id == block_id).first()
        if block:
            db.delete(block)
            return True
        return False


# --- Assignment Operations ---
def create_assignment(
    title: str,
    course_id: int,
    due_date: str,
    status: str = "Pending",
    priority: str = "Medium",
    notes: Optional[str] = None,
    submission_link: Optional[str] = None,
) -> Assignment:
    with get_db_session() as db:
        assignment = Assignment(
            title=title,
            course_id=course_id,
            due_date=due_date,
            status=status,
            priority=priority,
            notes=notes,
            submission_link=submission_link,
        )
        db.add(assignment)
        db.flush()
        db.refresh(assignment)
        return assignment


def update_assignment(
    assignment_id: int,
    title: str,
    course_id: int,
    due_date: str,
    priority: str = "Medium",
    notes: Optional[str] = None,
    submission_link: Optional[str] = None,
) -> Optional[Assignment]:
    with get_db_session() as db:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment:
            assignment.title = title
            assignment.course_id = course_id
            assignment.due_date = due_date
            assignment.priority = priority
            assignment.notes = notes
            assignment.submission_link = submission_link
            db.flush()
            db.refresh(assignment)
        return assignment


def get_assignments() -> List[Assignment]:
    with get_db_session() as db:
        return db.query(Assignment).options(joinedload(Assignment.course)).all()


def update_assignment_status(assignment_id: int, status: str) -> Optional[Assignment]:
    with get_db_session() as db:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment:
            assignment.status = status
            db.flush()
            db.refresh(assignment)
        return assignment


def delete_assignment(assignment_id: int) -> bool:
    with get_db_session() as db:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment:
            db.delete(assignment)
            return True
        return False


# --- DegreeRequirement Operations ---
def create_degree_requirement(
    course_code: str,
    prerequisite_code: Optional[str] = None,
    status: str = "Planned",
) -> DegreeRequirement:
    with get_db_session() as db:
        req = DegreeRequirement(
            course_code=course_code,
            prerequisite_code=prerequisite_code,
            status=status,
        )
        db.add(req)
        db.flush()
        db.refresh(req)
        return req


def get_degree_requirements() -> List[DegreeRequirement]:
    with get_db_session() as db:
        return db.query(DegreeRequirement).all()


def update_degree_requirement(
    req_id: int,
    course_code: str,
    prerequisite_code: Optional[str] = None,
) -> Optional[DegreeRequirement]:
    with get_db_session() as db:
        req = db.query(DegreeRequirement).filter(DegreeRequirement.id == req_id).first()
        if req:
            req.course_code = course_code
            req.prerequisite_code = prerequisite_code
            db.flush()
            db.refresh(req)
        return req


def update_degree_requirement_status(req_id: int, status: str) -> Optional[DegreeRequirement]:
    with get_db_session() as db:
        req = db.query(DegreeRequirement).filter(DegreeRequirement.id == req_id).first()
        if req:
            req.status = status
            db.flush()
            db.refresh(req)
        return req


def delete_degree_requirement(req_id: int) -> bool:
    with get_db_session() as db:
        req = db.query(DegreeRequirement).filter(DegreeRequirement.id == req_id).first()
        if req:
            db.delete(req)
            return True
        return False
