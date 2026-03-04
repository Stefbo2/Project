import streamlit as st

st.title("Taschenrechner")

tab1, tab2 = st.tabs(["Taschenrechner", "Sonstiges"])

with tab1:
    st.write("Hier kannst du deinen Taschenrechner verwenden. Führe Berechnungen durch, um deine Lerninhalte besser zu verstehen und anzuwenden.")  
    x = st.number_input("Gib eine Zahl ein:", value=0)
    y = st.number_input("Gib eine weitere Zahl ein:", value=0)
    operation = st.selectbox("Wähle eine Operation:", ["Addition", "Subtraktion", "Multiplikation", "Division"])
    if st.button("Berechnen"):
        if operation == "Addition":
            result = x + y
        elif operation == "Subtraktion":
            result = x - y
        elif operation == "Multiplikation":
            result = x * y
        elif operation == "Division":
            if y != 0:
                result = x / y
            else:
                result = "Fehler: Division durch Null"
        st.write(f"Ergebnis: {result}")

with tab2:
    st.write("Willkommen zu deinem Karteikarten-Tool! Hier kannst du deine Lerninhalte organisieren und effektiv lernen. Wähle einen Tab aus, um loszulegen.")

