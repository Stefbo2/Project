from collections import defaultdict

from database.db import get_connection
from services.payment_service import resolve_open_debts
from utils.helpers import minimize_transactions


def add_expense(
    group_id: int,
    description: str,
    amount: float,
    paid_by: int,
    expense_date: str,
    participant_ids: list[int],
    split_type: str = "equal",
) -> tuple[bool, str]:
    from datetime import datetime

    if not description.strip():
        return False, "Bitte eine Beschreibung eingeben."
    if amount <= 0:
        return False, "Der Betrag muss groesser als 0 sein."
    if not participant_ids:
        return False, "Mindestens ein beteiligtes Mitglied auswaehlen."
    if split_type != "equal":
        return False, "Aktuell wird nur die gleichmaessige Aufteilung unterstuetzt."

    share_amount = round(amount / len(participant_ids), 2)
    shares = [share_amount] * len(participant_ids)
    rounding_diff = round(amount - sum(shares), 2)
    shares[-1] = round(shares[-1] + rounding_diff, 2)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses (group_id, description, amount, paid_by, date, split_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                description.strip(),
                round(amount, 2),
                paid_by,
                expense_date,
                split_type,
                datetime.utcnow().isoformat(),
            ),
        )
        expense_id = cursor.lastrowid
        for user_id, owed_amount in zip(participant_ids, shares):
            connection.execute(
                """
                INSERT INTO expense_shares (expense_id, user_id, amount_owed)
                VALUES (?, ?, ?)
                """,
                (expense_id, user_id, owed_amount),
            )
        connection.commit()
    return True, "Ausgabe gespeichert."


def get_group_expenses(group_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT e.*, u.name AS paid_by_name
            FROM expenses e
            JOIN users u ON u.id = e.paid_by
            WHERE e.group_id = ?
            ORDER BY e.date DESC, e.id DESC
            """,
            (group_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_group_expense_shares(group_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                e.id AS expense_id,
                e.description,
                e.date,
                e.amount,
                payer.name AS paid_by_name,
                member.name AS member_name,
                es.user_id,
                es.amount_owed
            FROM expense_shares es
            JOIN expenses e ON e.id = es.expense_id
            JOIN users payer ON payer.id = e.paid_by
            JOIN users member ON member.id = es.user_id
            WHERE e.group_id = ?
            ORDER BY e.date DESC, e.id DESC
            """,
            (group_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_group_balances(group_id: int):
    debts, _ = resolve_open_debts()
    relevant = [debt for debt in debts if debt["group_id"] == group_id and debt["remaining_principal"] > 0]
    net = defaultdict(float)
    balance_rows = []
    for debt in relevant:
        total = debt["total_open_amount"]
        net[debt["debtor_id"]] -= total
        net[debt["creditor_id"]] += total
        balance_rows.append(
            {
                "Schuldner": debt["debtor_name"],
                "Glaeubiger": debt["creditor_name"],
                "Ursprungsbetrag": round(debt["original_amount"], 2),
                "Offener Betrag": round(debt["remaining_principal"], 2),
                "Verzugszinsen": round(debt["interest"], 2),
                "Gesamt offen": round(total, 2),
                "Seit": debt["expense_date"],
                "Beschreibung": debt["description"],
            }
        )

    settlements = minimize_transactions(net)
    settlements = [
        {
            "Von": item["from_name"],
            "An": item["to_name"],
            "Betrag": item["amount"],
        }
        for item in settlements
    ]
    return balance_rows, settlements


def get_user_dashboard_metrics(user_id: int):
    debts, _ = resolve_open_debts()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS cnt FROM group_members WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        groups_count = row["cnt"]

    owes = [debt for debt in debts if debt["debtor_id"] == user_id and debt["remaining_principal"] > 0]
    owed = [debt for debt in debts if debt["creditor_id"] == user_id and debt["remaining_principal"] > 0]
    overdue = [debt for debt in owes if debt["is_overdue"]]
    with_interest = [debt for debt in owes if debt["interest"] > 0]

    return {
        "groups_count": groups_count,
        "open_debts": round(sum(item["total_open_amount"] for item in owes), 2),
        "open_claims": round(sum(item["total_open_amount"] for item in owed), 2),
        "overdue_count": len(overdue),
        "interest_count": len(with_interest),
        "owes_items": owes,
        "owed_items": owed,
    }


def get_reliability_ranking():
    _, historical = resolve_open_debts()
    stats = defaultdict(lambda: {"paid": 0, "late": 0, "days": []})

    for item in historical:
        stats[item["debtor_id"]]["paid"] += 1
        stats[item["debtor_id"]]["days"].append(item["days_to_last_payment"])
        if item["days_to_last_payment"] > 14:
            stats[item["debtor_id"]]["late"] += 1

    with get_connection() as connection:
        users = connection.execute("SELECT id, name FROM users ORDER BY name").fetchall()

    ranking = []
    for user in users:
        user_stat = stats[user["id"]]
        avg_days = (
            sum(user_stat["days"]) / len(user_stat["days"])
            if user_stat["days"]
            else None
        )
        score = 100
        if avg_days is not None:
            score -= min(40, avg_days)
        score -= user_stat["late"] * 5
        ranking.append(
            {
                "Name": user["name"],
                "Bezahlte Schulden": user_stat["paid"],
                "Verspaetete Zahlungen": user_stat["late"],
                "Durchschnitt Tage": round(avg_days, 1) if avg_days is not None else None,
                "Zuverlaessigkeit": max(round(score, 1), 0),
            }
        )

    ranking.sort(key=lambda item: item["Zuverlaessigkeit"], reverse=True)
    return ranking
