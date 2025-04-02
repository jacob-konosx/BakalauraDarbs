import streamlit as st

st.set_page_config(layout="wide")

if "ir_satelita_flizes" not in st.session_state:
    st.session_state.ir_satelita_flizes = False

def pierakstisanas_logs():
    st.header("Šī aplikācija ir privāta.")
    st.subheader("Lūdzu pierakstieties.")
    st.button("Pierakstīties ar Google", on_click=st.login, icon="🔐")

if not st.experimental_user.is_logged_in:
    pierakstisanas_logs()
else:
    st.sidebar.button("❌ Izslēgt satelīta flīzes" if st.session_state.ir_satelita_flizes else "🗺️ Ieslēgt satelīta flīzes",
        on_click=lambda: st.session_state.update(ir_satelita_flizes=not st.session_state.ir_statelita_flizes),
        help="Opcija, kas ieslēdz satelīta attēla flīzes iekš ĢIS kartes"
    )

    st.sidebar.header(f"Sveicināti, {st.experimental_user.name}!")
    st.sidebar.button("Izrakstīties", icon="↪", on_click=st.logout)

    majas_lapa = st.Page("p_majas.py", title="Mājas", icon="🏠")
    tif_lapa = st.Page("p_tif.py", title="TIF Failu Apstrāde", icon="🔎")
    sensoru_lapa = st.Page("p_sensori.py", title="Sensoru Dati", icon="📡")

    pg = st.navigation([majas_lapa, tif_lapa, sensoru_lapa])

    pg.run()
