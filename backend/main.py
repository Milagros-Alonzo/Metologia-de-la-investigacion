from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
import os

app = FastAPI(title="TaskFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "taskflow"),
    "user": os.getenv("DB_USER", "taskuser"),
    "password": os.getenv("DB_PASSWORD", "taskpass"),
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.on_event("startup")
def startup():
    import time
    for i in range(10):
        try:
            init_db()
            print("DB ready")
            break
        except Exception as e:
            print(f"DB not ready, retrying... ({i+1}/10): {e}")
            time.sleep(3)

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TaskUpdate(BaseModel):
    completed: bool

@app.get("/")
def root():
    return {"message": "TaskFlow API running"}

@app.get("/tasks")
def get_tasks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, completed, created_at FROM tasks ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "description": r[2], "completed": r[3], "created_at": str(r[4])}
        for r in rows
    ]

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description) VALUES (%s, %s) RETURNING id",
        (task.title, task.description)
    )
    task_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": task_id, "title": task.title, "description": task.description, "completed": False}

@app.patch("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed=%s WHERE id=%s RETURNING id", (task.completed, task_id))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    conn.commit()
    cur.close()
    conn.close()
    return {"id": task_id, "completed": task.completed}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s RETURNING id", (task_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    conn.commit()
    cur.close()
    conn.close()
    return {"deleted": task_id}
