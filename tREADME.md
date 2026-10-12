# Flet Student Portal

A modern, desktop and web student portal application built by **Arty Belanger** ([@coding-with-arty](https://github.com/coding-with-arty)) using **Python 3.10+**, **Flet** (Material Design 3), and **SQLAlchemy 2.0**.

Designed around modular UI architectures and clean database abstraction, this portal delivers an intuitive, dark-mode academic workspace with local SQLite persistence.

---

## 🌟 Key Features

- **📊 Academic Dashboard**: High-level overview displaying enrolled course lists, upcoming coursework deadlines, and degree completion metrics.
- **📅 Interactive Weekly Schedule**:
  - Daily timetable grids organized by day of the week.
  - Weekend toggle switch (show/hide Saturday and Sunday columns).
  - Flexible typable course inputs for custom class numbers and names.
  - Full CRUD operations (add, edit, and delete schedule blocks).
- **📋 Assignments Kanban Board**:
  - Three-column workflow board (*To-Do*, *In Progress*, *Submitted*).
  - Dynamic deadline badges (*Overdue*, *Due Today*, *Upcoming*).
  - Custom coursework notes and instructions.
  - Online submission link inputs with one-click portal launching.
- **🎓 Degree Pathway Auditor**:
  - Requirement roadmap with visual locked indicators for prerequisite dependencies.
  - Editable credit goal targets (e.g., 120, 128 credits).
  - Enrollment degree contract file attachment (`.pdf`, `.docx`, `.png`) to safeguard graduation requirements from catalog changes.
- **⚙️ Profile Settings**:
  - Student identity management (Name, Student ID, Major, Email).
  - Persistent storage committed to local SQLite database across app sessions.

---

## 🛠️ Project Structure

The project follows a clean, modular architecture separating presentation views, reusable components, data models, and styling utilities:

```text
├── src/
│   ├── components/
│   │   └── app_bar.py         # Standardized navigation top app bar & dark/light toggle
│   ├── database/
│   │   ├── connection.py      # SQLite connection, session management, & schema migration
│   │   ├── crud.py            # Transactional database CRUD functions
│   │   └── models.py          # SQLAlchemy 2.0 ORM data models
│   ├── utils/
│   │   └── theme.py           # Material Design 3 theme configurations & alignment helpers
│   ├── views/
│   │   ├── assignments_view.py # Kanban coursework board with notes & submission links
│   │   ├── dashboard_view.py   # Overview dashboard & high-level academic metrics
│   │   ├── degree_view.py      # Prerequisite audit map & contract document vault
│   │   ├── schedule_view.py    # Weekly class timetable with weekend toggling
│   │   └── settings_view.py    # Student profile management & persistence
│   └── main.py                # Main application entry point, routing, & navigation rail
├── requirements.txt           # Dependency requirements
├── student_app.db             # Local SQLite database (auto-generated)
└── README.md                  # Project documentation
```

---

## 🚀 Tech Stack

* **GUI Framework**: [Flet](https://flet.dev/) (Material Design 3, Dark Mode default)
* **Database / ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) with SQLite (`student_app.db`)
* **Language**: Python 3.10+
* **Author**: Arty Belanger ([coding-with-arty](https://github.com/coding-with-arty))

---

## ⚡ Quickstart & Installation

1. **Clone the Repository**:
```bash
git clone [https://github.com/coding-with-arty/student-portal.git](https://github.com/coding-with-arty/student-portal.git)
cd student-portal

```

2. **Set Up a Virtual Environment**:
* **Windows**:
```cmd
python -m venv venv
venv\Scripts\activate

```

* **macOS / Linux**:
```bash
python3 -m venv venv
source venv/bin/activate

```


3. **Install Dependencies**:
```bash
pip install -r requirements.txt

```

4. **Run the Application**:
```bash
python src/main.py

```


*Note: On initial startup, `init_db()` automatically provisions `student_app.db` and applies automated schema migrations for missing table columns without data loss.*

---

## 📦 Packaging & Distribution

Deploy or build standalone cross-platform binaries using the Flet CLI:

* **Windows Executable**:
```bash
flet build windows

```

* **macOS Application**:
```bash
flet build macos

```

* **Web App**:
```bash
flet build web

```

---

## 📄 License

Distributed under the MIT License. Created by [Arty Belanger](https://github.com/coding-with-arty).

```

```
