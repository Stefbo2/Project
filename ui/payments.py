from datetime import date

import pandas as pd
import streamlit as st

from services.payment_service import get_all_payments_for_user, get_user_debts, record_payment


def render_payments_page(user: dict) -> None:
    st.title("Zahlungen")
    debts = get_user_debts(user["id"])

    st.subheader("Offene Schulden begleichen")
    owe_options = [
        (
            f"{row['group_name']}: an {row['creditor_name']} | {row['description']} | {row['total_open_amount']:.2f} EUR",
            row,
        )
        for row in debts["owes"]
    ]

    if owe_options:
        labels = [item[0] for item in owe_options]
        selected_label = st.selectbox("Offene Schuld", labels)
        selected_debt = dict(owe_options)[selected_label]
        default_amount = float(selected_debt["total_open_amount"])
        with st.form("payment_form"):
            amount = st.number_input(
                "Zahlungsbetrag",
                min_value=0.01,
                max_value=default_amount,
                value=default_amount,
                step=1.0,
            )
            payment_date = st.date_input("Zahlungsdatum", value=date.today())
            submitted = st.form_submit_button("Zahlung speichern", use_container_width=True)
        if submitted:
            success, message = record_payment(
                group_id=selected_debt["group_id"],
                from_user=user["id"],
                to_user=selected_debt["creditor_id"],
                amount=float(amount),
                payment_date=payment_date.isoformat(),
                related_expense_id=selected_debt["expense_id"],
            )
            if success:
                st.success(message)
                st.rerun()
            st.error(message)
    else:
        st.success("Keine offenen Schulden zum Begleichen.")

    st.subheader("Zahlungshistorie")
    history = pd.DataFrame(get_all_payments_for_user(user["id"]))
    if history.empty:
        st.info("Noch keine Zahlungen vorhanden.")
        return

    st.dataframe(
        history.rename(
            columns={
                "group_name": "Gruppe",
                "from_name": "Von",
                "to_name": "An",
                "amount": "Betrag",
                "payment_date": "Zahlungsdatum",
            }
        )[["Gruppe", "Von", "An", "Betrag", "Zahlungsdatum"]],
        use_container_width=True,
        hide_index=True,
    )
