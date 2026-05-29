# AI Time Manager

A web application for task management and work-time tracking with AI-powered productivity analysis powered by Claude (Anthropic).

## Features

### Task Management
- Create, edit, and delete tasks
- Categories: `work`, `study`, `health`, `personal`, `other`
- Statuses: `pending` / `completed`
- Set deadlines and estimated completion time
- Filtering and pagination of the task list
- View overdue incomplete tasks

### Timer
- Start/stop timer for each task
- **Pomodoro** mode (25-minute work sessions)
- Manual time entry with notes
- View active timers

### Analytics
- Statistics for a selected period (default — 30 days):
  - total number of sessions and hours
  - average session duration
  - activity distribution by time of day (morning / afternoon / evening)
  - most productive day of the week
  - percentage of completed and overdue tasks
  - top category by time spent
  - **productivity index** (0–100, custom metric)
  - number of Pomodoro sessions
- Export statistics as JSON
- **AI analysis** — personalised recommendations from Claude:
  - short productivity summary
  - productivity score (1–10)
  - 4–5 actionable tips
  - detected behavioural patterns
- AI analysis history

### Authentication
- Registration and login via JWT token
- Profile editing (name)

### Administration
- List of all users with task counts
- View tasks of any user
- Endpoint protection via `is_admin` flag

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, **FastAPI** |
| ORM / DB | **SQLAlchemy** 2.x, **SQLite** |
| Authentication | JWT (`python-jose`), password hashing (`passlib[bcrypt]`) |
| AI | **Anthropic Claude** (`claude-sonnet-4-6`) |
| Frontend | Vanilla JS, HTML/CSS (SPA, served via `StaticFiles`) |
| Tests | **pytest**, **httpx** (async test client) |
| Configuration | `pydantic-settings`, `python-dotenv` |

## Project Structure

```
AI_Time_Manager/
├── main.py                  # entry point, FastAPI app
├── database.py              # SQLAlchemy connection
├── requirements.txt
├── .env.example
├── core/
│   ├── config.py            # settings from .env
│   ├── security.py          # JWT, password hashing
│   └── dependencies.py      # get_db, get_current_user, get_admin_user
├── models/                  # SQLAlchemy models
│   ├── user.py
│   ├── task.py
│   ├── time_log.py
│   └── ai_analysis.py
├── schemas/                 # Pydantic schemas (request/response)
│   ├── user.py
│   ├── task.py
│   ├── time_log.py
│   └── ai_analysis.py
├── repositories/            # SQL queries
│   ├── user_repo.py
│   ├── task_repo.py
│   ├── time_log_repo.py
│   └── ai_analysis_repo.py
├── services/                # business logic
│   ├── auth_service.py
│   ├── task_service.py
│   ├── time_log_service.py
│   ├── ai_service.py        # Anthropic API calls
│   └── stats_service.py     # statistics calculation
├── routes/                  # FastAPI routers
│   ├── auth.py
│   ├── tasks.py
│   ├── timer.py
│   ├── analytics.py
│   └── admin.py
├── static/                  # frontend (SPA)
│   ├── index.html
│   ├── app.js
│   └── style.css
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_tasks.py
    ├── test_timer.py
    ├── test_analytics.py
    └── test_admin.py
```

## Getting Started

### 1. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the values:

```env
SECRET_KEY=your-long-random-string
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=sqlite:///./time_manager.db
```

### 3. Run the server

```bash
uvicorn main:app --reload
```

Application available at: `http://127.0.0.1:8000`

Interactive API docs: `http://127.0.0.1:8000/docs`

## Tests

```bash
pytest
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register |
| `POST` | `/auth/login` | Login, receive JWT |
| `GET` | `/auth/me` | Current user data |
| `GET` | `/tasks` | List tasks (pagination, filters) |
| `POST` | `/tasks` | Create task |
| `PUT` | `/tasks/{id}` | Update task |
| `DELETE` | `/tasks/{id}` | Delete task |
| `POST` | `/tasks/{id}/complete` | Mark as completed |
| `GET` | `/tasks/overdue` | Overdue tasks |
| `POST` | `/tasks/{id}/timer/start` | Start timer (`?pomodoro=true`) |
| `POST` | `/tasks/{id}/timer/stop` | Stop timer |
| `POST` | `/tasks/{id}/timer/manual` | Manual time entry |
| `GET` | `/analytics/stats` | Statistics (`?days=30`) |
| `POST` | `/analytics/ai-analysis` | Run AI analysis |
| `GET` | `/analytics/ai-analysis` | AI analysis history |
| `GET` | `/analytics/export` | Export statistics as JSON |
| `GET` | `/admin/users` | List users (admin) |
| `GET` | `/admin/users/{id}/tasks` | User tasks (admin) |
