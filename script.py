import streamlit as st

def pierakstisanas_logs():
    st.header("Šī aplikācija ir privāta.")
    st.subheader("Lūdzu pierakstieties.")
    st.button("Pierakstīties ar Google", on_click=st.login, icon="🔐")

if not st.experimental_user.is_logged_in:
    pierakstisanas_logs()
else:
    st.sidebar.header(f"Sveicināti, {st.experimental_user.name}!")
    if st.sidebar.button("Izrakstīties", icon="↪"):
        st.logout()

    majas = st.Page("majas.py", title="Mājas", icon="🏠")

    tif_lapa = st.Page("tifs.py", title="Apskatīt TIF", icon="🔎")

    pg = st.navigation([majas, tif_lapa])

    pg.run()
