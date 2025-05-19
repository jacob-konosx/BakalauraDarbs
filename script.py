import json
import streamlit as st
from st_cookies_manager import EncryptedCookieManager
from utils.pieprasijumi import dabut_galveni, izveidot_projektu
from utils.stils import dabut_stilu
from utils.db import db_dabut_lietotaju_pec_epasta, db_vai_pilnvarots_epasts, db_izveidot_lietotaju

st.set_page_config(layout="wide")

stils = dabut_stilu()
st.markdown(stils, unsafe_allow_html=True)

if "izrakstities" not in st.session_state:
    st.session_state.izrakstities = False

def izrakstit_lietotaju(sikdatne):
    sikdatne["odm_projekta_id"] = ""
    sikdatne["galvene"] = ""
    st.session_state.izrakstities = True
    st.rerun()

def iestatit_galveni(sikdatne):
    galvene = dabut_galveni()

    if galvene:
        sikdatne["galvene"] = json.dumps(galvene)
        st.toast("WebODM savienots veiksmīgi.", icon="✅")
    else:
        st.toast("Neizdevās savienoties ar WebODM.", icon="❌")

    return galvene

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
        galvene = iestatit_galveni(sikdatne)
        if not galvene:
            st.header("Neizdevās savienot ar ODM API.")
            st.text("ODM ir kritiska sistēmas komponente. Lūdzu mēģiniet savienoties, lai turpinātu tīmekļa vietnes darbību.")
            if st.button("Savienot ar ODM", icon="🔄"):
                st.rerun()
            st.stop()
    if "galvene" not in st.session_state:
        st.session_state.galvene = json.loads(sikdatne["galvene"])

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
    if "odm_projekta_id" not in st.session_state:
        st.session_state.odm_projekta_id = sikdatne["odm_projekta_id"]

    st.sidebar.button("Atiestatīt WebODM žetonu", icon="🔄", on_click=iestatit_galveni, args=(sikdatne,),)
    st.sidebar.header(f"Sveicināti, :blue[{st.user.name}]!")
    st.sidebar.button("Izrakstīties", icon="↪", on_click=izrakstit_lietotaju, args=(sikdatne,))

    majas_lapa = st.Page("lapas/ortofoto_izveide.py", title="Ortofoto izveide", icon="🪡")
    tif_izvele = st.Page("lapas/ortofoto_parvalde.py", title="Mani ortofoto", icon="🗺️")
    sensoru_lapa = st.Page("lapas/sensoru_dati.py", title="Sensoru dati", icon="📡")
    pg = st.navigation({"Kartes": [majas_lapa, tif_izvele], "Dati": [sensoru_lapa]})

    pg.run()
