import json
import streamlit as st
from st_cookies_manager import EncryptedCookieManager
from lietotajs import iestatit_lietotaju
from pieprasijumi import dabut_galveni

VIENA_DIENA = 86400

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        div.st-key-CookieManager-sync_cookies{
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

if "ir_satelita_flizes" not in st.session_state:
    st.session_state.ir_satelita_flizes = False
    st.session_state.izrakstities = False

def uzstadit_odm_savienojumu(sikdatne):
    galvene = dabut_galveni()
    if galvene:
        sikdatne["galvene"] = galvene
        st.toast("ODM savienots veiksmīgi.", icon="✅")

def izrakstit_lietotaju(sikdatne):
    sikdatne["odm_projekta_id"] = ""
    sikdatne["galvene"] = ""
    st.session_state.izrakstities = True
    st.rerun()

sikdatne = EncryptedCookieManager(
    prefix="st_",
    password=st.secrets.sikdatnes_parole,
)
if not sikdatne.ready():
    st.stop()
st.session_state.sikdatne = sikdatne

if not st.experimental_user.is_logged_in:
    st.header("Tīmekļa vietne ir privāta")
    st.text("Lūdzu pierakstieties, lai turpinātu tīmekļa vietnes darbību.")
    st.button("Pierakstīties ar Google", on_click=st.login, icon="🔐")
else:
    if st.session_state.izrakstities:
        st.logout()

    if "galvene" not in sikdatne or not sikdatne["galvene"]:
        uzstadit_odm_savienojumu(sikdatne)
    if "galvene" not in sikdatne or not sikdatne["galvene"]:
        st.header("Neizdevās savienot ar ODM API.")
        st.text("ODM ir kritiska sistēmas komponente. Lūdzu mēģiniet savienoties, lai turpinātu tīmekļa vietnes darbību.")
        st.button("Savienot ar ODM", icon="🔄", on_click=uzstadit_odm_savienojumu, args=(sikdatne,))
        st.stop()

    if "galvene" not in st.session_state:
        st.session_state.galvene = json.loads(sikdatne["galvene"])

    if "odm_projekta_id" not in sikdatne or not sikdatne["odm_projekta_id"]:
        projekta_id = iestatit_lietotaju()
        sikdatne["odm_projekta_id"] = projekta_id
    if "odm_projekta_id" not in st.session_state:
        st.session_state.odm_projekta_id = sikdatne["odm_projekta_id"]

    st.sidebar.header(f"Sveicināti, {st.experimental_user.name}!")
    st.sidebar.button("❌ Izslēgt satelīta flīzes" if st.session_state.ir_satelita_flizes else "🗺️ Ieslēgt satelīta flīzes",
        on_click=lambda: st.session_state.update(ir_satelita_flizes=not st.session_state.ir_satelita_flizes),
        help="Opcija, kas ieslēdz satelīta attēla flīzes iekš ĢIS kartes"
    )
    st.sidebar.button("Izrakstīties", icon="↪", on_click=izrakstit_lietotaju, args=(sikdatne,))

    majas_lapa = st.Page("pages/kartes_izveide.py", title="Kartes izveide", icon="🪡")
    tif_izvele = st.Page("pages/tif_parvalde.py", title="GeoTIFF Kartes", icon="🗺️")
    sensoru_lapa = st.Page("pages/sensoru_dati.py", title="Sensoru Dati", icon="📡")

    pg = st.navigation([majas_lapa, tif_izvele, sensoru_lapa])

    pg.run()
