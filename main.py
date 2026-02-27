import psycopg2
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    # Подключение к базе данных PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname="sikn_db", 
            user="sikn_db_user", 
            password="KTOKMH", 
            host="sikn-db.onrender.com",  # Правильный хост для базы данных
            port="5432"  # Порт для PostgreSQL
        )
        return conn
    except Exception as e:
        # Ошибка подключения к базе данных
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


def init_db():
    # Инициализация базы данных
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Создание таблицы пользователей, если не существует
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
            """)

            # Создание таблицы ячеек, если не существует
            cur.execute("""
            CREATE TABLE IF NOT EXISTS cells(
                row INTEGER,
                col INTEGER,
                value TEXT
            )
            """)

            # Очистка таблицы пользователей
            cur.execute("DELETE FROM users")

            # Вставка пользователя
            cur.execute(
                "INSERT INTO users(username, password) VALUES(%s, %s)",
                ("SIKN", "KTOKMH")
            )

            # Сохранение изменений
            conn.commit()
    finally:
        conn.close()


# Инициализация базы данных при запуске
init_db()


@app.get("/")
def index():
    # Отправка файла index.html
    return FileResponse("templates/index.html")


@app.post("/login")
async def login(req: Request):
    # Логин пользователя
    data = await req.json()
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    try:
        with db.cursor() as cur:
            # Проверка пользователя в базе данных
            cur.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password)
            )

            user = cur.fetchone()

        if not user:
            return {"error": "Invalid login"}

        # Установка cookie для авторизации
        res = JSONResponse(content={"ok": True})
        res.set_cookie(key="user", value=username)
        return res
    finally:
        db.close()


@app.post("/logout")
async def logout():
    # Логаут пользователя
    res = JSONResponse(content={"ok": True})
    res.delete_cookie("user")
    return res


@app.post("/save_cell")
async def save_cell(req: Request):
    # Сохранение данных ячейки в базе данных
    data = await req.json()

    row = data["row"]
    col = data["col"]
    value = data["value"]

    db = get_db()
    try:
        with db.cursor() as cur:
            # Удаление старых значений из таблицы
            cur.execute("DELETE FROM cells WHERE row=%s AND col=%s", (row, col))
            # Вставка новых данных в таблицу
            cur.execute(
                "INSERT INTO cells(row, col, value) VALUES(%s, %s, %s)",
                (row, col, value)
            )
        
        # Сохранение изменений в базе данных
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@app.get("/load_cells")
async def load_cells():
    # Загрузка всех ячеек из базы данных
    db = get_db()
    try:
        with db.cursor() as cur:
            # Запрос для получения всех ячеек
            cur.execute("SELECT row, col, value FROM cells")
            rows = cur.fetchall()

        # Возвращение данных в виде списка словарей
        return [
            {"row": r[0], "col": r[1], "value": r[2]}
            for r in rows
        ]
    finally:
        db.close()
