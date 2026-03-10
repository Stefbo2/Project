from collections import defaultdict
from datetime import datetime

from database.db import get_connection
from services.interest_service import calculate_interest
from utils.helpers import set_user_name_lookup


def record_payment(
    group_id: int,
    from_user: int,
    to_user: int,
    amount: float,
    payment_date: str,
    related_expense_id: int | None = None,
) -> tuple[bool, str]:
    if amount <= 0:
        return False, "Der Zahlungsbetrag muss groesser als 0 sein."

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO payments (
                group_id, from_user, to_user, amount, payment_date, related_expense_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                from_user,
                to_user,
                round(amount, 2),
                payment_date,
                related_expense_id,
                datetime.utcnow().isoformat(),
            ),
        )
        connection.commit()
    return True, "Zahlung gespeichert."


def get_group_payments(group_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.*, fu.name AS from_name, tu.name AS to_name
            FROM payments p
            JOIN users fu ON fu.id = p.from_user
            JOIN users tu ON tu.id = p.to_user
            WHERE p.group_id = ?
            ORDER BY p.payment_date DESC, p.id DESC
            """,
            (group_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_payments_for_user(user_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.*, g.name AS group_name, fu.name AS from_name, tu.name AS to_name
            FROM payments p
            JOIN groups_table g ON g.id = p.group_id
            JOIN users fu ON fu.id = p.from_user
            JOIN users tu ON tu.id = p.to_user
            WHERE p.from_user = ? OR p.to_user = ?
            ORDER BY p.payment_date DESC, p.id DESC
            """,
            (user_id, user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def _fetch_debt_rows():
    with get_connection() as connection:
        debts = connection.execute(
            """
            SELECT
                e.group_id,
                e.id AS expense_id,
                e.description,
                e.date AS expense_date,
                es.user_id AS debtor_id,
                e.paid_by AS creditor_id,
                es.amount_owed AS original_amount
            FROM expense_shares es
            JOIN expenses e ON e.id = es.expense_id
            WHERE es.user_id != e.paid_by
            ORDER BY e.date, e.id, es.id
            """
        ).fetchall()
        payments = connection.execute(
            """
            SELECT *
            FROM payments
            ORDER BY payment_date, id
            """
        ).fetchall()
        users = connection.execute("SELECT id, name FROM users").fetchall()
        groups = connection.execute("SELECT id, name FROM groups_table").fetchall()

    user_lookup = {row["id"]: row["name"] for row in users}
    set_user_name_lookup(user_lookup)
    return (
        [dict(row) for row in debts],
        [dict(row) for row in payments],
        user_lookup,
        {row["id"]: row["name"] for row in groups},
    )


def resolve_open_debts():
    debts, payments, user_names, group_names = _fetch_debt_rows()
    payment_buckets = defaultdict(list)
    for payment in payments:
        key = (payment["group_id"], payment["from_user"], payment["to_user"])
        payment_buckets[key].append(
            {
                "remaining": float(payment["amount"]),
                "payment_date": payment["payment_date"],
                "payment_id": payment["id"],
            }
        )

    resolved = []
    historical = []

    for debt in debts:
        key = (debt["group_id"], debt["debtor_id"], debt["creditor_id"])
        remaining = float(debt["original_amount"])
        allocations = []
        for payment in payment_buckets[key]:
            if remaining <= 0:
                break
            if payment["remaining"] <= 0:
                continue
            applied = min(remaining, payment["remaining"])
            if applied > 0:
                payment["remaining"] = round(payment["remaining"] - applied, 2)
                remaining = round(remaining - applied, 2)
                allocations.append(
                    {
                        "payment_id": payment["payment_id"],
                        "payment_date": payment["payment_date"],
                        "amount": round(applied, 2),
                    }
                )

        paid_amount = round(float(debt["original_amount"]) - remaining, 2)
        interest_info = calculate_interest(remaining, debt["expense_date"])
        record = {
            **debt,
            "debtor_name": user_names.get(debt["debtor_id"], "Unknown"),
            "creditor_name": user_names.get(debt["creditor_id"], "Unknown"),
            "group_name": group_names.get(debt["group_id"], "Unknown"),
            "remaining_principal": round(remaining, 2),
            "paid_amount": paid_amount,
            "payment_allocations": allocations,
            "interest": interest_info["interest"] if remaining > 0 else 0.0,
            "days_open": interest_info["days_open"],
            "overdue_days": interest_info["overdue_days"],
            "is_overdue": interest_info["is_overdue"] and remaining > 0,
            "total_open_amount": (
                interest_info["total_with_interest"] if remaining > 0 else 0.0
            ),
        }
        resolved.append(record)

        if allocations:
            last_payment_date = allocations[-1]["payment_date"]
            total_days = (
                datetime.fromisoformat(last_payment_date).date()
                - datetime.fromisoformat(debt["expense_date"]).date()
            ).days
            historical.append(
                {
                    "expense_id": debt["expense_id"],
                    "group_id": debt["group_id"],
                    "debtor_id": debt["debtor_id"],
                    "creditor_id": debt["creditor_id"],
                    "amount": float(debt["original_amount"]),
                    "paid_amount": paid_amount,
                    "days_to_first_payment": (
                        datetime.fromisoformat(allocations[0]["payment_date"]).date()
                        - datetime.fromisoformat(debt["expense_date"]).date()
                    ).days,
                    "days_to_last_payment": total_days,
                    "is_fully_paid": remaining <= 0,
                }
            )

    return resolved, historical


def get_user_debts(user_id: int) -> dict:
    debts, _ = resolve_open_debts()
    user_owes = [debt for debt in debts if debt["debtor_id"] == user_id and debt["remaining_principal"] > 0]
    user_is_owed = [debt for debt in debts if debt["creditor_id"] == user_id and debt["remaining_principal"] > 0]
    return {"owes": user_owes, "owed": user_is_owed}
