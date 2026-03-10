from datetime import datetime

from database.db import get_connection


def create_group(name: str, creator_id: int) -> tuple[bool, str]:
    if not name.strip():
        return False, "Der Gruppenname darf nicht leer sein."

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO groups_table (name, created_by, created_at)
            VALUES (?, ?, ?)
            """,
            (name.strip(), creator_id, datetime.utcnow().isoformat()),
        )
        group_id = cursor.lastrowid
        connection.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, creator_id),
        )
        connection.commit()
    return True, "Gruppe erfolgreich erstellt."


def add_member_by_email(group_id: int, email: str) -> tuple[bool, str]:
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        if not user:
            return False, "Kein Benutzer mit dieser E-Mail gefunden."

        connection.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, user["id"]),
        )
        connection.commit()
    return True, "Mitglied hinzugefuegt."


def get_user_groups(user_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT g.*, u.name AS creator_name
            FROM groups_table g
            JOIN group_members gm ON gm.group_id = g.id
            JOIN users u ON u.id = g.created_by
            WHERE gm.user_id = ?
            ORDER BY g.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_group_by_id(group_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT g.*, u.name AS creator_name
            FROM groups_table g
            JOIN users u ON u.id = g.created_by
            WHERE g.id = ?
            """,
            (group_id,),
        ).fetchone()
    return dict(row) if row else None


def get_group_members(group_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT u.id, u.name, u.email
            FROM group_members gm
            JOIN users u ON u.id = gm.user_id
            WHERE gm.group_id = ?
            ORDER BY u.name
            """,
            (group_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def user_in_group(group_id: int, user_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        ).fetchone()
    return row is not None
