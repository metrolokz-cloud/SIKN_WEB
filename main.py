from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    return sqlite3.connect("database.db")


def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        "INSERT INTO users(username,password) VALUES(?,?)",
        ("SIKN", "KTOKMH")
    )

    conn.commit()
    conn.close()


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
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cur.fetchone()
    db.close()

    if not user:
        return {"error": "Invalid login"}

    res = JSONResponse(content={"ok": True})
    res.set_cookie(key="user", value=username)
    return res


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
    cur = db.cursor()

    cur.execute("DELETE FROM cells WHERE row=? AND col=?", (row, col))
    cur.execute(
        "INSERT INTO cells(row,col,value) VALUES(?,?,?)",
        (row, col, value)
    )

    db.commit()
    db.close()

    return {"ok": True}


@app.get("/load_cells")
async def load_cells():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT row,col,value FROM cells")
    rows = cur.fetchall()
    db.close()

    return [
        {"row": r[0], "col": r[1], "value": r[2]}
        for r in rows
    ]
