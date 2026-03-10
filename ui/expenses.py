from datetime import date

import pandas as pd
import streamlit as st

from services.expense_service import add_expense, get_group_expense_shares
from services.group_service import get_group_members, get_user_groups


def render_expenses_page(user: dict) -> None:
    st.title("Ausgabe hinzufuegen")
    groups = get_user_groups(user["id"])
    if not groups:
        st.info("Bitte zuerst eine Gruppe erstellen.")
        return

    group_options = {f"{group['name']} (#{group['id']})": group["id"] for group in groups}
    selected_label = st.selectbox("Gruppe", list(group_options.keys()))
    group_id = group_options[selected_label]
    st.session_state["selected_group_id"] = group_id

    members = get_group_members(group_id)
    member_lookup = {member["name"]: member["id"] for member in members}

    with st.form("expense_form"):
        description = st.text_input("Beschreibung")
        amount = st.number_input("Betrag", min_value=0.01, step=1.0)
        expense_date = st.date_input("Datum", value=date.today())
        paid_by = st.selectbox("Wer hat bezahlt?", list(member_lookup.keys()))
        participants = st.multiselect(
            "Beteiligte Mitglieder",
            list(member_lookup.keys()),
            default=list(member_lookup.keys()),
        )
        submitted = st.form_submit_button("Ausgabe speichern", use_container_width=True)

    if submitted:
        success, message = add_expense(
            group_id=group_id,
            description=description,
            amount=float(amount),
            paid_by=member_lookup[paid_by],
            expense_date=expense_date.isoformat(),
            participant_ids=[member_lookup[name] for name in participants],
        )
        if success:
            st.success(message)
            st.rerun()
        st.error(message)

    st.subheader("Verteilung der Ausgaben")
    shares_frame = pd.DataFrame(get_group_expense_shares(group_id))
    if shares_frame.empty:
        st.caption("Noch keine Anteile vorhanden.")
    else:
        st.dataframe(
            shares_frame.rename(
                columns={
                    "description": "Beschreibung",
                    "date": "Datum",
                    "amount": "Gesamtbetrag",
                    "paid_by_name": "Bezahlt von",
                    "member_name": "Mitglied",
                    "amount_owed": "Anteil",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
