import json
import streamlit as st
from st_cookies_manager import EncryptedCookieManager
from lietotajs import iestatit_lietotaju
from pieprasijumi import savienot_odm

st.set_page_config(layout="wide")

VIENA_DIENA = 86400

if "ir_satelita_flizes" not in st.session_state:
    st.session_state.ir_satelita_flizes = False

def uzstadit_odm_savienojumu(sikdatne):
    galvene = savienot_odm()
    sikdatne["galvene"] = galvene

sikdatne = EncryptedCookieManager(
    prefix="st_",
    password=st.secrets.sikdatnes_parole,
)
if not sikdatne.ready():
    st.stop()

if not st.experimental_user.is_logged_in:
    st.header("Tīmekļa vietne ir privāta")
    st.text("Lūdzu pierakstieties, lai turpinātu tīmekļa vietnes darbību.")
    st.button("Pierakstīties ar Google", on_click=st.login, icon="🔐")
else:
    if "odm_projekta_id" not in sikdatne:
        projekta_id = iestatit_lietotaju()
        galvene = savienot_odm()

        sikdatne["odm_projekta_id"] = projekta_id
        sikdatne["galvene"] = galvene

    if "galvene" not in sikdatne:
        st.header("Neizdevās savienot ar ODM API.")
        st.text("ODM ir kritiska sistēmas komponente. Lūdzu mēģiniet savienoties, lai turpinātu tīmekļa vietnes darbību.")
        st.button("Savienot ar ODM", icon="🔄", on_click=uzstadit_odm_savienojumu, args=(sikdatne,))
        st.stop()

    if "odm_projekta_id" not in st.session_state:
        st.session_state.odm_projekta_id = sikdatne["odm_projekta_id"]
        st.session_state.galvene = json.loads(sikdatne["galvene"])

    st.sidebar.button("❌ Izslēgt satelīta flīzes" if st.session_state.ir_satelita_flizes else "🗺️ Ieslēgt satelīta flīzes",
        on_click=lambda: st.session_state.update(ir_satelita_flizes=not st.session_state.ir_satelita_flizes),
        help="Opcija, kas ieslēdz satelīta attēla flīzes iekš ĢIS kartes"
    )
    st.sidebar.header(f"Sveicināti, {st.experimental_user.name}!")
    st.sidebar.button("Izrakstīties", icon="↪", on_click=st.logout)

    majas_lapa = st.Page("lapas/kartes_izveide.py", title="Kartes izveide", icon="🗺️")
    tif_lapa = st.Page("lapas/tif.py", title="TIF Failu Apstrāde", icon="🔎")
    sensoru_lapa = st.Page("lapas/sensoru_dati.py", title="Sensoru Dati", icon="📡")

    pg = st.navigation([majas_lapa, tif_lapa, sensoru_lapa])

    pg.run()
