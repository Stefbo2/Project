import streamlit as st

from services.auth_service import authenticate_user, register_user


def render_auth_page() -> None:
    col1, col2 = st.columns([1.1, 0.9])
    with col1:
        st.title("SmartSplit")
        st.subheader("Gemeinsame Ausgaben klar verwalten")
        st.markdown(
            """
            <div class="smart-card">
            SmartSplit ist ein MVP fuer Gruppen-Ausgaben, Salden, Verzugszinsen und eine einfache ML-Prognose zur Rueckzahlungsdauer.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Demo-Login: alice@smartsplit.local / Password123!")

    with col2:
        login_tab, register_tab = st.tabs(["Login", "Registrierung"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("E-Mail")
                password = st.text_input("Passwort", type="password")
                submitted = st.form_submit_button("Einloggen", use_container_width=True)
            if submitted:
                user = authenticate_user(email, password)
                if user:
                    st.session_state["user_id"] = user["id"]
                    st.success("Login erfolgreich.")
                    st.rerun()
                st.error("Ungueltige E-Mail oder Passwort.")

        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Name")
                email = st.text_input("E-Mail", key="register_email")
                password = st.text_input("Passwort", type="password", key="register_password")
                submitted = st.form_submit_button("Registrieren", use_container_width=True)
            if submitted:
                success, message = register_user(name, email, password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
