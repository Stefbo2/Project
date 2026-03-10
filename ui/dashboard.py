import pandas as pd
import streamlit as st

from services.expense_service import get_reliability_ranking, get_user_dashboard_metrics
from services.ml_service import estimate_repayment_for_user


def render_dashboard_page(user: dict) -> None:
    st.title("Dashboard")
    metrics = get_user_dashboard_metrics(user["id"])
    estimate = estimate_repayment_for_user(user["id"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Gruppen", metrics["groups_count"])
    col2.metric("Offene Forderungen", f"{metrics['open_claims']:.2f} EUR")
    col3.metric("Offene Schulden", f"{metrics['open_debts']:.2f} EUR")
    col4.metric("Ueberfaellige Schulden", metrics["overdue_count"])
    col5.metric("Mit Zinsen", metrics["interest_count"])

    if estimate["predictions"]:
        avg_prediction = sum(item["estimated_days"] for item in estimate["predictions"]) / len(estimate["predictions"])
        st.metric("Geschaetzte Rueckzahlungsdauer", f"{avg_prediction:.0f} Tage")
    else:
        st.caption(estimate["message"] or "Keine offenen Schulden vorhanden.")

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Meine offenen Verbindlichkeiten")
        owes_frame = pd.DataFrame(
            [
                {
                    "Gruppe": row["group_name"],
                    "An": row["creditor_name"],
                    "Beschreibung": row["description"],
                    "Offen": row["remaining_principal"],
                    "Zinsen": row["interest"],
                    "Gesamt": row["total_open_amount"],
                }
                for row in metrics["owes_items"]
            ]
        )
        if owes_frame.empty:
            st.success("Keine offenen Schulden.")
        else:
            st.dataframe(owes_frame, use_container_width=True, hide_index=True)

        st.subheader("Meine offenen Forderungen")
        owed_frame = pd.DataFrame(
            [
                {
                    "Gruppe": row["group_name"],
                    "Von": row["debtor_name"],
                    "Beschreibung": row["description"],
                    "Offen": row["remaining_principal"],
                    "Zinsen": row["interest"],
                    "Gesamt": row["total_open_amount"],
                }
                for row in metrics["owed_items"]
            ]
        )
        if owed_frame.empty:
            st.info("Aktuell keine offenen Forderungen.")
        else:
            st.dataframe(owed_frame, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Ranking verlaesslicher Zahler")
        ranking = pd.DataFrame(get_reliability_ranking())
        st.dataframe(ranking, use_container_width=True, hide_index=True)
