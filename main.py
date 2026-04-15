# venv\Scripts\activate
# uvicorn main:app --reload


import time
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routes import auth, tasks, timer, analytics, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

# Міграція --> додаєmся is_admin якщо стовпець відсутній 
from sqlalchemy import inspect, text
with engine.connect() as conn:
    columns = [c["name"] for c in inspect(engine).get_columns("users")]
    if "is_admin" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
        conn.commit()

app = FastAPI(
    title="AI Time Manager",
    description="Система тайм-менеджменту з ШІ-аналізом звичок",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# middleware для логування часу відповіді
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)")
    return response


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(timer.router)
app.include_router(analytics.router)
app.include_router(admin.router)

# Фронтенд
app.mount("/", StaticFiles(directory="static", html=True), name="static")



