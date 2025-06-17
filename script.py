import json
import streamlit as st
from st_cookies_manager import EncryptedCookieManager
from api.pieprasijumi import iestatit_galveni, izveidot_projektu
from utils.stils import dabut_stilu
from db.db import db_dabut_lietotaju_pec_epasta, db_vai_pilnvarots_epasts, db_izveidot_lietotaju

st.set_page_config(layout="wide")

stils = dabut_stilu()
st.markdown(stils, unsafe_allow_html=True)

if "izrakstities" not in st.session_state:
    st.session_state.izrakstities = False

def izrakstit_lietotaju():
    st.session_state.sikdatne["odm_projekta_id"] = ""
    st.session_state.sikdatne["galvene"] = ""
    st.session_state.izrakstities = True

sikdatne = EncryptedCookieManager(
    prefix="st_",
    password=st.secrets.sikdatnes_parole,
)
if not sikdatne.ready():
    st.stop()
st.session_state.sikdatne = sikdatne

if not st.user.is_logged_in:
    st.header("Tīmekļa vietne ir privāta")
    st.text("Lūdzu pierakstieties, lai turpinātu tīmekļa vietnes darbību.")
    st.button("Pierakstīties ar Google", on_click=st.login, icon="🔐")
else:
    if st.session_state.izrakstities:
        st.logout()

    if "galvene" not in sikdatne or not sikdatne["galvene"]:
        ir_galvene_iestatita = iestatit_galveni()

        if ir_galvene_iestatita:
            st.toast("WebODM savienots veiksmīgi.", icon="✅")
        else:
            st.toast("Neizdevās savienoties ar WebODM.", icon="❌")

            st.header("Neizdevās savienot ar ODM API.")
            st.text("ODM ir kritiska sistēmas komponente. Lūdzu mēģiniet savienoties, lai turpinātu tīmekļa vietnes darbību.")
            if st.button("Savienot ar ODM", icon="🔄"):
                st.rerun()
            st.stop()

    if "odm_projekta_id" not in sikdatne or not sikdatne["odm_projekta_id"]:
        projekta_id = None

        db_lietotajs = db_dabut_lietotaju_pec_epasta()
        if not db_lietotajs:
            if db_vai_pilnvarots_epasts():
                izveidotais_projekts = izveidot_projektu()

                if izveidotais_projekts:
                    projekta_id = izveidotais_projekts["id"]
                    db_izveidot_lietotaju(projekta_id)
            else:
                st.header("Konts nav pilnvarots")
                st.info("Jūsu e-pasta adrese nav pilnvarota sitēmā. Sazinaties ar tīmekļa lietotnes administratoru, lai pilnvarotu Jūsu e-pasta adresi.", icon="ℹ️")

                st.button("Mēģiniet vēlreiz autentificēties", icon="🔐", on_click=st.logout)
                st.stop()
        else:
            projekta_id = db_lietotajs["projekta_id"]

        sikdatne["odm_projekta_id"] = str(projekta_id)

    st.sidebar.header(f"Sveicināti, :blue[{st.user.name}]!")
    st.sidebar.button("Izrakstīties", icon="↪", on_click=izrakstit_lietotaju)

    ortofoto_izveide = st.Page("pages/ortofoto_izveide.py", title="Ortofoto izveide", icon="🪡")
    ortofoto_parvalde = st.Page("pages/ortofoto_parvalde.py", title="Mani ortofoto", icon="🗺️")
    sensoru_dati = st.Page("pages/sensoru_dati.py", title="Sensoru dati", icon="📡")
    pg = st.navigation({"Ortofoto": [ortofoto_izveide, ortofoto_parvalde], "Sensora Dati": [sensoru_dati]})

    pg.run()
