from datetime import datetime

from database.db import get_connection
from utils.security import hash_password, verify_password


def register_user(name: str, email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not name.strip() or not email or len(password) < 8:
        return False, "Bitte Name, E-Mail und ein Passwort mit mindestens 8 Zeichen angeben."

    password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name.strip(), email, password_hash, datetime.utcnow().isoformat()),
            )
            connection.commit()
        return True, "Registrierung erfolgreich."
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return False, "Diese E-Mail ist bereits registriert."
        return False, f"Registrierung fehlgeschlagen: {exc}"


def authenticate_user(email: str, password: str):
    email = email.strip().lower()
    with get_connection() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if user and verify_password(password, user["password_hash"]):
        return dict(user)
    return None


def get_user_by_id(user_id: int):
    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(user) if user else None


def list_users():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, email, created_at FROM users ORDER BY name"
        ).fetchall()
    return [dict(row) for row in rows]
