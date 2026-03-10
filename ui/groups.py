import pandas as pd
import streamlit as st

from services.expense_service import get_group_balances, get_group_expenses
from services.group_service import (
    add_member_by_email,
    create_group,
    get_group_by_id,
    get_group_members,
    get_user_groups,
    user_in_group,
)


def _group_selector(user_id: int, label: str):
    groups = get_user_groups(user_id)
    if not groups:
        return None, []

    group_map = {f"{group['name']} (#{group['id']})": group["id"] for group in groups}
    default_index = 0
    if st.session_state.get("selected_group_id") in [group["id"] for group in groups]:
        current = st.session_state["selected_group_id"]
        default_index = list(group_map.values()).index(current)

    selection = st.selectbox(label, list(group_map.keys()), index=default_index)
    selected_group_id = group_map[selection]
    st.session_state["selected_group_id"] = selected_group_id
    return selected_group_id, groups


def render_groups_page(user: dict) -> None:
    st.title("Meine Gruppen")
    selected_group_id, groups = _group_selector(user["id"], "Gruppe auswaehlen")
    left, right = st.columns([0.9, 1.1])

    with left:
        st.subheader("Neue Gruppe")
        with st.form("create_group_form"):
            group_name = st.text_input("Gruppenname")
            submitted = st.form_submit_button("Gruppe erstellen", use_container_width=True)
        if submitted:
            success, message = create_group(group_name, user["id"])
            if success:
                st.success(message)
                st.rerun()
            st.error(message)

        if selected_group_id:
            st.subheader("Mitglied hinzufuegen")
            with st.form("add_member_form"):
                email = st.text_input("E-Mail des Mitglieds")
                member_submit = st.form_submit_button("Hinzufuegen", use_container_width=True)
            if member_submit:
                success, message = add_member_by_email(selected_group_id, email)
                if success:
                    st.success(message)
                    st.rerun()
                st.error(message)

    with right:
        st.subheader("Meine Gruppenliste")
        if not groups:
            st.info("Noch keine Gruppen vorhanden.")
            return

        group_frame = pd.DataFrame(
            [
                {
                    "ID": group["id"],
                    "Name": group["name"],
                    "Erstellt von": group["creator_name"],
                    "Erstellt am": group["created_at"][:10],
                }
                for group in groups
            ]
        )
        st.dataframe(group_frame, use_container_width=True, hide_index=True)

        if selected_group_id:
            group = get_group_by_id(selected_group_id)
            members = pd.DataFrame(get_group_members(selected_group_id))
            st.markdown(
                f"""
                <div class="smart-card">
                <strong>{group['name']}</strong><br>
                Erstellt von: {group['creator_name']}<br>
                Mitglieder: {len(members)}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.dataframe(members.rename(columns={"name": "Name", "email": "E-Mail"}), use_container_width=True, hide_index=True)


def render_group_detail_page(user: dict) -> None:
    st.title("Gruppendetail")
    selected_group_id, groups = _group_selector(user["id"], "Gruppe")
    if not groups:
        st.info("Bitte zuerst eine Gruppe erstellen.")
        return
    if not selected_group_id or not user_in_group(selected_group_id, user["id"]):
        st.warning("Keine gueltige Gruppe ausgewaehlt.")
        return

    group = get_group_by_id(selected_group_id)
    expenses = pd.DataFrame(get_group_expenses(selected_group_id))
    balances, settlements = get_group_balances(selected_group_id)
    members = pd.DataFrame(get_group_members(selected_group_id))

    st.subheader(group["name"])
    top_left, top_right = st.columns([0.8, 1.2])
    with top_left:
        st.dataframe(
            members.rename(columns={"name": "Name", "email": "E-Mail"}),
            use_container_width=True,
            hide_index=True,
        )
    with top_right:
        st.write("**Transaktionsvorschlaege zur Minimierung**")
        if settlements:
            st.dataframe(pd.DataFrame(settlements), use_container_width=True, hide_index=True)
        else:
            st.success("Alle Salden sind ausgeglichen.")

    st.write("**Offene Salden**")
    if balances:
        st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)
    else:
        st.info("Keine offenen Salden in dieser Gruppe.")

    st.write("**Ausgabenhistorie**")
    if expenses.empty:
        st.info("Noch keine Ausgaben vorhanden.")
    else:
        st.dataframe(
            expenses.rename(
                columns={
                    "description": "Beschreibung",
                    "amount": "Betrag",
                    "paid_by_name": "Bezahlt von",
                    "date": "Datum",
                    "split_type": "Aufteilung",
                }
            )[["Beschreibung", "Betrag", "Bezahlt von", "Datum", "Aufteilung"]],
            use_container_width=True,
            hide_index=True,
        )
