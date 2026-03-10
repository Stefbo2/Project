from datetime import date, timedelta

from database.db import get_connection
from utils.security import hash_password


def seed_demo_data() -> None:
    with get_connection() as connection:
        existing = connection.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if existing["cnt"] > 0:
            return

        users = [
            ("Alice", "alice@smartsplit.local", "Password123!"),
            ("Bob", "bob@smartsplit.local", "Password123!"),
            ("Carla", "carla@smartsplit.local", "Password123!"),
            ("David", "david@smartsplit.local", "Password123!"),
        ]
        user_ids = {}
        for name, email, password in users:
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, hash_password(password), date.today().isoformat()),
            )
            user_ids[name] = cursor.lastrowid

        group_cursor = connection.execute(
            """
            INSERT INTO groups_table (name, created_by, created_at)
            VALUES (?, ?, ?)
            """,
            ("WG Sommersemester", user_ids["Alice"], date.today().isoformat()),
        )
        group_id = group_cursor.lastrowid

        for user_id in user_ids.values():
            connection.execute(
                "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id),
            )

        expenses = [
            ("Wocheneinkauf", 84.0, "Alice", date.today() - timedelta(days=28), ["Alice", "Bob", "Carla", "David"]),
            ("Pizzaabend", 48.0, "Bob", date.today() - timedelta(days=19), ["Alice", "Bob", "Carla"]),
            ("Streaming-Abo", 18.0, "Carla", date.today() - timedelta(days=10), ["Alice", "Carla", "David"]),
            ("Putzmittel", 24.0, "David", date.today() - timedelta(days=5), ["Bob", "Carla", "David"]),
        ]

        expense_ids = {}
        for description, amount, payer_name, expense_date, members in expenses:
            cursor = connection.execute(
                """
                INSERT INTO expenses (group_id, description, amount, paid_by, date, split_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_id,
                    description,
                    amount,
                    user_ids[payer_name],
                    expense_date.isoformat(),
                    "equal",
                    expense_date.isoformat(),
                ),
            )
            expense_id = cursor.lastrowid
            expense_ids[description] = expense_id
            share = round(amount / len(members), 2)
            shares = [share] * len(members)
            shares[-1] = round(shares[-1] + (amount - sum(shares)), 2)
            for member_name, share_amount in zip(members, shares):
                connection.execute(
                    """
                    INSERT INTO expense_shares (expense_id, user_id, amount_owed)
                    VALUES (?, ?, ?)
                    """,
                    (expense_id, user_ids[member_name], share_amount),
                )

        payments = [
            (group_id, "Bob", "Alice", 21.0, date.today() - timedelta(days=20), expense_ids["Wocheneinkauf"]),
            (group_id, "Carla", "Alice", 10.5, date.today() - timedelta(days=15), expense_ids["Wocheneinkauf"]),
            (group_id, "Alice", "Bob", 16.0, date.today() - timedelta(days=6), expense_ids["Pizzaabend"]),
            (group_id, "David", "Carla", 6.0, date.today() - timedelta(days=2), expense_ids["Streaming-Abo"]),
        ]

        for group_id_value, from_name, to_name, amount, payment_date, related_expense_id in payments:
            connection.execute(
                """
                INSERT INTO payments (
                    group_id, from_user, to_user, amount, payment_date, related_expense_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_id_value,
                    user_ids[from_name],
                    user_ids[to_name],
                    amount,
                    payment_date.isoformat(),
                    related_expense_id,
                    payment_date.isoformat(),
                ),
            )

        connection.commit()
