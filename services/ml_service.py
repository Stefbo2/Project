from collections import defaultdict

import pandas as pd
from sklearn.linear_model import LinearRegression

from services.payment_service import resolve_open_debts


def _build_training_frame():
    open_debts, historical = resolve_open_debts()
    by_user = defaultdict(list)
    for item in historical:
        by_user[item["debtor_id"]].append(item)

    records = []
    for debtor_id, items in by_user.items():
        items = sorted(items, key=lambda row: row["days_to_last_payment"])
        previous_delayed = 0
        previous_avg = 7.0
        for index, item in enumerate(items):
            prior_items = items[:index]
            if prior_items:
                previous_avg = sum(x["days_to_last_payment"] for x in prior_items) / len(prior_items)
                previous_delayed = sum(1 for x in prior_items if x["days_to_last_payment"] > 14)

            records.append(
                {
                    "debtor_id": debtor_id,
                    "amount": item["amount"],
                    "late_count": previous_delayed,
                    "avg_previous_days": previous_avg,
                    "open_debts_count": sum(1 for debt in open_debts if debt["debtor_id"] == debtor_id),
                    "target_days": max(item["days_to_last_payment"], 1),
                }
            )

    if len(records) < 6:
        records.extend(
            [
                {"debtor_id": 0, "amount": 18, "late_count": 0, "avg_previous_days": 6, "open_debts_count": 1, "target_days": 5},
                {"debtor_id": 0, "amount": 45, "late_count": 1, "avg_previous_days": 10, "open_debts_count": 2, "target_days": 12},
                {"debtor_id": 0, "amount": 90, "late_count": 2, "avg_previous_days": 16, "open_debts_count": 3, "target_days": 24},
                {"debtor_id": 0, "amount": 35, "late_count": 0, "avg_previous_days": 8, "open_debts_count": 1, "target_days": 7},
                {"debtor_id": 0, "amount": 120, "late_count": 3, "avg_previous_days": 20, "open_debts_count": 4, "target_days": 33},
                {"debtor_id": 0, "amount": 60, "late_count": 1, "avg_previous_days": 9, "open_debts_count": 2, "target_days": 14},
            ]
        )

    return pd.DataFrame(records), open_debts, historical


def train_repayment_model():
    frame, open_debts, historical = _build_training_frame()
    if frame.empty:
        return None, None, open_debts, historical

    model = LinearRegression()
    feature_columns = ["amount", "late_count", "avg_previous_days", "open_debts_count"]
    model.fit(frame[feature_columns], frame["target_days"])
    return model, feature_columns, open_debts, historical


def estimate_repayment_for_user(user_id: int):
    model, feature_columns, open_debts, historical = train_repayment_model()
    if model is None:
        return {"message": "Nicht genug Daten fuer eine Schaetzung vorhanden.", "predictions": []}

    user_history = [item for item in historical if item["debtor_id"] == user_id]
    late_count = sum(1 for item in user_history if item["days_to_last_payment"] > 14)
    avg_days = (
        sum(item["days_to_last_payment"] for item in user_history) / len(user_history)
        if user_history
        else 9.0
    )
    user_open_debts = [item for item in open_debts if item["debtor_id"] == user_id and item["remaining_principal"] > 0]

    predictions = []
    for debt in user_open_debts:
        features = pd.DataFrame(
            [
                {
                    "amount": debt["remaining_principal"],
                    "late_count": late_count,
                    "avg_previous_days": avg_days,
                    "open_debts_count": len(user_open_debts),
                }
            ]
        )
        estimated_days = max(1, round(float(model.predict(features[feature_columns])[0])))
        predictions.append(
            {
                "group_name": debt["group_name"],
                "creditor_name": debt["creditor_name"],
                "description": debt["description"],
                "open_amount": round(debt["total_open_amount"], 2),
                "estimated_days": estimated_days,
            }
        )

    message = None if predictions else "Aktuell gibt es keine offenen Schulden fuer eine Schaetzung."
    return {"message": message, "predictions": predictions}
