import time
import streamlit as st
from utils.pieprasijumi import izdzest_uzdevumu_pec_id, dabut_uzdevuma_info_pec_id, sakt_uzdevumu_pec_id, izveidot_karti, augsupieladet_odm_attelus_pec_id
from utils.db import izveidot_odm_uzdevumu, dzest_odm_uzdevumu_pec_id

GRUPU_IZMERS = 5

if "uzdevuma_id" not in st.session_state:
    st.session_state.uploader_key = 0
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.session_state.uzdevums_augsupielade = False


def atiestatit_datus():
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.rerun()

def generet_karti(faili, kartes_nosaukums, ortofoto_izskirtspeja, izveletais_datums):
    dati = izveidot_karti(kartes_nosaukums, ortofoto_izskirtspeja)

    if dati:
        st.session_state.uzdevuma_id = dati["id"]
        st.session_state.uzdevums_augsupielade = True
        st.session_state.uploader_key += 1
        st.session_state.faili = faili

        izveidot_odm_uzdevumu(st.session_state.uzdevuma_id, izveletais_datums)

def atcelt_uzdevumu():
    dzest_odm_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    izdzest_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.session_state.uzdevums_augsupielade = False

st.title("Ortofoto izveide")
if st.session_state.uzdevums_augsupielade:
    faili = st.session_state.faili
    failu_skaits = len(faili)

    progresa_text = "Drona attēli tiek augšupielādēti uz WebODM. Lūdzu uzgaidiet un nepametiet šo lapu!"
    col1, col2 = st.columns([5, 1.5])

    with col1:
        progresa_josla = st.progress(0, text=progresa_text)
    with col2:
        st.button("Atcelt kartes izveidi", on_click=atcelt_uzdevumu, icon="❌")

    for indeks, fails in enumerate(faili):
        atteli = [("images", (fails.name, fails, fails.type))]

        augsupieladet_odm_attelus_pec_id(st.session_state.uzdevuma_id, atteli)

        progress = indeks / (failu_skaits - 1)
        progresa_josla.progress(progress, progresa_text)

    sakt_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    st.session_state.uzdevums_augsupielade = False
    st.session_state.uzdevums_aktivs = True
    st.rerun()
elif st.session_state.uzdevums_aktivs:
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

            st.toast("Karte tika veiksmīgi izveidota.", icon="✅")
            atiestatit_datus()
            st.switch_page("lapas/ortofoto_parvalde.py")
    else:
        atiestatit_datus()
else:
    kartes_nosaukums = st.text_input("Kartes Nosaukums", placeholder="Ievadiet kartes nosaukumu", max_chars=100)
    ortofoto_izskirtspeja = st.slider("⚙️ Ortofoto izšķirtspēja", min_value=0.0, step=0.5, max_value=5.0, value=3.5, help="5.0 - maksimālā izšķirtspēja, 0.5 - minimālā izšķirtspeja", format="%0.1f")
    izveletais_datums = st.date_input("Izvēlaties ortofoto datumu:", format="DD.MM.YYYY", value=None)
    izveleti_faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)

    st.button("📤 Ģenerēt karti", on_click=generet_karti, args=(izveleti_faili, kartes_nosaukums, 5-ortofoto_izskirtspeja, izveletais_datums), disabled=kartes_nosaukums=="" or izveleti_faili==[] or izveletais_datums==None)
