import time, zipfile, mimetypes
from io import BytesIO
import streamlit as st
from utils.pieprasijumi import izdzest_uzdevumu_pec_id, dabut_uzdevuma_info_pec_id, sakt_uzdevumu_pec_id, izveidot_karti, augsupieladet_odm_attelus_pec_id
from utils.db import db_izveidot_odm_uzdevumu, db_dzest_odm_uzdevumu_pec_id

if "uzdevuma_id" not in st.session_state:
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
        st.session_state.faili = faili

        db_izveidot_odm_uzdevumu(st.session_state.uzdevuma_id, izveletais_datums)

def atcelt_uzdevumu():
    db_dzest_odm_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    izdzest_uzdevumu_pec_id(st.session_state.uzdevuma_id)
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.session_state.uzdevums_augsupielade = False


st.title("Ortofoto izveide")
ievades_bloks = st.empty()
augsupielades_bloks = st.empty()
apstrades_bloks = st.empty()

if st.session_state.uzdevums_augsupielade:
    failu_skaits = len(st.session_state.faili)

    progresa_text = "📤 Drona attēli tiek augšupielādēti iekš WebODM. Lūdzu uzgaidiet."
    with augsupielades_bloks.container():
        col1, col2 = st.columns([5, 1.5])

        with col1:
            progresa_josla = st.progress(0, text=progresa_text)
        with col2:
            st.button("Atcelt kartes izveidi", on_click=atcelt_uzdevumu, icon="❌")

        for indeks, fails in enumerate(st.session_state.faili):
            progress = indeks / (failu_skaits - 1)
            progresa_josla.progress(progress, progresa_text)

            atteli = [("images", (fails.name, fails, fails.type))]
            augsupieladet_odm_attelus_pec_id(st.session_state.uzdevuma_id, atteli)
        else:
            sakt_uzdevumu_pec_id(st.session_state.uzdevuma_id)
            st.session_state.uzdevums_augsupielade = False
            st.session_state.uzdevums_aktivs = True
            st.rerun()
elif st.session_state.uzdevums_aktivs:
    progresa_text = "🪡 Notiek ortofoto izveide. Lūdzu uzgaidiet."

    with apstrades_bloks.container():
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
    with ievades_bloks.container():
        kartes_nosaukums = st.text_input("Kartes Nosaukums", placeholder="Ievadiet kartes nosaukumu", max_chars=100)
        ortofoto_izskirtspeja = st.slider("⚙️ Ortofoto izšķirtspēja", min_value=0.0, step=0.5, max_value=5.0, value=3.0, help="5.0 - maksimālā izšķirtspēja, 0.0 - minimālā izšķirtspeja", format="%0.1f")
        izveletais_datums = st.date_input("Izvēlaties ortofoto datumu:", format="DD.MM.YYYY", value=None)
        izveletais_zip = st.file_uploader("Izvēlieties .ZIP failu, kas satur drona attēlus::", type=["zip"])

        atteli = []

        if izveletais_zip:
            with zipfile.ZipFile(izveletais_zip) as zip_ref:
                for fila_nosaukums in zip_ref.namelist():
                    if fila_nosaukums.lower().endswith((".png", ".jpg", ".jpeg")):
                        with zip_ref.open(fila_nosaukums) as fails:
                            faila_baiti = BytesIO(fails.read())

                            faila_baiti.name = fila_nosaukums
                            faila_baiti.type = mimetypes.guess_type(fila_nosaukums)[0] or "application/octet-stream"

                            atteli.append(faila_baiti)

        st.button("📤 Ģenerēt karti", on_click=generet_karti, args=(atteli, kartes_nosaukums, 5-ortofoto_izskirtspeja, izveletais_datums), disabled=kartes_nosaukums=="" or atteli==[] or izveletais_datums==None)
