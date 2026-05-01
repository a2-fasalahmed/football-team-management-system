# Football Team Management System
**Module:**  Software Development Project  

A web-based football team management system allowing coaches and players 
to manage fixtures, track availability, and organise team activities.

## Setup & Installation
1. Clone the repository: `git clone https://github.com/a2-fasalahmed/football-team-management-system`
2. Navigate to the project: `cd football-team-management-system`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate it: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Create a `.env` file with: `SECRET_KEY=any-random-string`
7. Run database migrations: `flask db upgrade`
8. Run the app: `flask run`
9. Open browser at: `http://localhost:5000/index`

## Running Tests
```bash
python -m pytest tests/ -v
```

## Tech Stack
- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend:** Jinja2, Bootstrap 5, HTML, CSS
- **Database:** SQLite
- **Version Control:** Git / GitHub
