from database.init_db import initialize_database
from services.auth_service import get_user_by_id
from ui.auth_pages import render_auth_page
from ui.dashboard import render_dashboard_page
from ui.expenses import render_expenses_page
from ui.groups import render_group_detail_page, render_groups_page
from ui.ml_analysis import render_ml_analysis_page
from ui.payments import render_payments_page
import streamlit as st


def _init_session() -> None:
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("selected_group_id", None)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 145, 255, 0.12), transparent 30%),
                radial-gradient(circle at top right, rgba(0, 200, 120, 0.12), transparent 28%),
                linear-gradient(180deg, #f6f9fc 0%, #edf3f8 100%);
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 0.8rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }
        .smart-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 1.2rem;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="SmartSplit", layout="wide")
    initialize_database()
    _init_session()
    _apply_theme()

    if not st.session_state["user_id"]:
        render_auth_page()
        return

    user = get_user_by_id(st.session_state["user_id"])
    if not user:
        st.session_state["user_id"] = None
        st.rerun()

    with st.sidebar:
        st.title("SmartSplit")
        st.caption(f"Angemeldet als {user['name']}")
        page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Meine Gruppen",
                "Gruppendetail",
                "Ausgabe hinzufuegen",
                "Zahlungen",
                "ML-Analyse",
            ],
        )
        if st.button("Logout", use_container_width=True):
            st.session_state["user_id"] = None
            st.session_state["selected_group_id"] = None
            st.rerun()

    if page == "Dashboard":
        render_dashboard_page(user)
    elif page == "Meine Gruppen":
        render_groups_page(user)
    elif page == "Gruppendetail":
        render_group_detail_page(user)
    elif page == "Ausgabe hinzufuegen":
        render_expenses_page(user)
    elif page == "Zahlungen":
        render_payments_page(user)
    else:
        render_ml_analysis_page(user)


if __name__ == "__main__":
    main()
