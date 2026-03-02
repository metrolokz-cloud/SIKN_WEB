import os
import psycopg2
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL not set")

    return psycopg2.connect(database_url)


def init_db():
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS cells(
            row INTEGER,
            col INTEGER,
            value TEXT
        )
        """)

        cur.execute("DELETE FROM users")

        cur.execute(
            "INSERT INTO users(username, password) VALUES(%s, %s)",
            ("SIKN", "KTOKMH")
        )

        conn.commit()
        cur.close()
    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def index():
    return FileResponse("templates/index.html")


@app.post("/login")
async def login(req: Request):
    data = await req.json()
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    try:
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cur.fetchone()
        cur.close()

        if not user:
            return {"error": "Invalid login"}

        res = JSONResponse(content={"ok": True})
        res.set_cookie(key="user", value=username)
        return res
    finally:
        db.close()


@app.post("/logout")
async def logout():
    res = JSONResponse(content={"ok": True})
    res.delete_cookie("user")
    return res


@app.post("/save_cell")
async def save_cell(req: Request):
    data = await req.json()

    row = data["row"]
    col = data["col"]
    value = data["value"]

    db = get_db()
    try:
        cur = db.cursor()

        cur.execute("DELETE FROM cells WHERE row=%s AND col=%s", (row, col))
        cur.execute(
            "INSERT INTO cells(row, col, value) VALUES(%s, %s, %s)",
            (row, col, value)
        )

        db.commit()
        cur.close()
        return {"ok": True}
    finally:
        db.close()


@app.get("/load_cells")
async def load_cells():
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT row, col, value FROM cells")
        rows = cur.fetchall()
        cur.close()

        return [
            {"row": r[0], "col": r[1], "value": r[2]}
            for r in rows
        ]
    finally:
        db.close()
