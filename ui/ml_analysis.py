import pandas as pd
import streamlit as st

from services.ml_service import estimate_repayment_for_user
from services.payment_service import resolve_open_debts


def render_ml_analysis_page(user: dict) -> None:
    st.title("ML-Analyse")
    st.caption("Lineare Regression auf Basis historischer Zahlungen und Demo-Daten.")

    estimates = estimate_repayment_for_user(user["id"])
    if estimates["message"] and not estimates["predictions"]:
        st.info(estimates["message"])

    if estimates["predictions"]:
        st.subheader("Geschaetzte Rueckzahlungsdauer")
        frame = pd.DataFrame(estimates["predictions"]).rename(
            columns={
                "group_name": "Gruppe",
                "creditor_name": "Glaeubiger",
                "description": "Beschreibung",
                "open_amount": "Offener Betrag",
                "estimated_days": "Geschaetzte Tage",
            }
        )
        st.dataframe(frame, use_container_width=True, hide_index=True)

    open_debts, historical = resolve_open_debts()
    user_history = [item for item in historical if item["debtor_id"] == user["id"]]

    left, right = st.columns(2)
    with left:
        st.metric("Historische Zahlungen", len(user_history))
        avg_days = (
            sum(item["days_to_last_payment"] for item in user_history) / len(user_history)
            if user_history
            else 0
        )
        st.metric("Durchschnittliche Rueckzahlung", f"{avg_days:.1f} Tage")
    with right:
        late_count = sum(1 for item in user_history if item["days_to_last_payment"] > 14)
        st.metric("Verspaetete Zahlungen", late_count)
        current_open = sum(1 for item in open_debts if item["debtor_id"] == user["id"] and item["remaining_principal"] > 0)
        st.metric("Aktuelle offene Schulden", current_open)
