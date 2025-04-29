import time
import streamlit as st
from utils.pieprasijumi import izdzest_uzdevumu_pec_id, dabut_uzdevuma_info_pec_id, izveidot_karti

if "uzdevuma_id" not in st.session_state:
    st.session_state.uploader_key = 0
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False

def generet_karti(faili, kartes_nosaukums, ortofoto_izskirtspeja):
    atteli = [("images", (fails.name, fails.getvalue(), fails.type)) for fails in faili]
    dati = izveidot_karti(atteli, kartes_nosaukums, ortofoto_izskirtspeja)

    if dati:
        st.session_state.uzdevuma_id = dati["id"]
        st.session_state.uzdevums_aktivs = True
        st.session_state.uploader_key += 1
        st.toast("Attēli veiksmīgi augšupielādēti ODM.", icon="📤")

def atiestatit_datus():
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False

def atcelt_uzdevumu():
    izdzest_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False

st.title("Kartes GeoTIFF izveide")
if not st.session_state.uzdevums_aktivs:
    kartes_nosaukums = st.text_input("Kartes Nosaukums", placeholder="Ievadiet kartes nosaukumu", max_chars=100)
    ortofoto_izskirtspeja = st.slider("⚙️ Ortofoto izšķirtspēja", min_value=0.0, step=0.5, max_value=5.0, value=4.0, help="5.0 - maksimālā izšķirtspēja, 0.5 - minimālā izšķirtspeja", format="%0.1f")
    izveleti_faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)

    st.button("📤 Ģenerēt karti", on_click=generet_karti, args=(izveleti_faili, kartes_nosaukums, 5-ortofoto_izskirtspeja), disabled=kartes_nosaukums=="" or izveleti_faili==[])
else:
    progresa_text = "Notiek kartes izveidošana. Lūdzu uzgaidiet."
    col1, col2 = st.columns([5, 1.5])

    with col1:
        progresa_josla = st.progress(0, text=progresa_text)
    with col2:
        st.button("Atcelt kartes izveidi", on_click=atcelt_uzdevumu, icon="❌")

    uzdevuma_dati = dabut_uzdevuma_info_pec_id(st.session_state.uzdevuma_id)
    if uzdevuma_dati:
        while not uzdevuma_dati["status"] == 40:
            progress = uzdevuma_dati["running_progress"]
            progresa_josla.progress(progress, text=progresa_text)

            time.sleep(5)
            uzdevuma_dati = dabut_uzdevuma_info_pec_id(st.session_state.uzdevuma_id)
    else:
        atiestatit_datus()
        st.rerun()

    st.toast("Karte tika veiksmīgi izveidota.", icon="✅")

    st.session_state.uzdevums_aktivs = False
    st.switch_page("lapas/kartes_parvalde.py")
