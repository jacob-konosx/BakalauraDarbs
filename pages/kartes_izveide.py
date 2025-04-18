import time
import streamlit as st
from pieprasijumi import izdzest_karti_pec_id, dabut_kartes_info, izveidot_karti

st.markdown(
    """
    <style>
        div[data-testid="stFileUploaderDropzoneInstructions"] div span, small {
            display: none;
        }

        div[data-testid="stFileUploaderDropzoneInstructions"] div::after {
            content: "Izvēlēties drona JPG failus (200MB faila limits)";
        }

        section[data-testid="stFileUploaderDropzone"]{
            cursor: pointer;
        }

        div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="stBaseButton-secondary"] {
            display: none;
        }
    <style>
    """, unsafe_allow_html=True)

if "uzdevuma_id" not in st.session_state:
    st.session_state.uploader_key = 0
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.session_state.ir_karte_izveidota = False

def generet_karti(faili, kartes_nosaukums):
    atteli = [("images", (fails.name, fails.getvalue(), fails.type)) for fails in faili]
    ir_izveidots = izveidot_karti(atteli, kartes_nosaukums)

    if ir_izveidots:
        st.toast("Attēli veiksmīgi augšupielādēti ODM.", icon="📤")

def atiestatit_datus():
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False
    st.session_state.ir_karte_izveidota = False

def atcelt_uzdevumu():
    izdzest_karti_pec_id(st.session_state.uzdevuma_id)
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False

st.title("Kartes GeoTIFF izveide")

izveleti_faili = None
if not st.session_state.uzdevums_aktivs:
    if st.session_state.ir_karte_izveidota:
        col1, col2 = st.columns([5, 1.5])

        with col1:
            st.subheader("GeoTIFF karte veiksmīgi izveidota!")
            st.page_link("pages/tif_parvalde.py", label="Atvērt karti", icon="🔎")
        with col2:
            st.button("Veidot jaunu karti", on_click=atiestatit_datus, icon="❌")
    else:
        kartes_nosaukums = st.text_input("Kartes Nosaukums", placeholder="Ievadiet kartes nosaukumu")
        izveleti_faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)
        if izveleti_faili and kartes_nosaukums:
            st.button("📤 Ģenerēt karti", on_click=generet_karti, args=(izveleti_faili, kartes_nosaukums))
else:
    progresa_text = "Notiek kartes izveidošana. Lūdzu uzgaidiet."
    col1, col2 = st.columns([5, 1.5])

    with col1:
        progresa_josla = st.progress(0, text=progresa_text)
    with col2:
        st.button("Atcelt kartes izveidi", on_click=atcelt_uzdevumu, icon="❌")

    uzdevuma_dati = dabut_kartes_info()
    while not uzdevuma_dati["status"] == 40:
        progress = uzdevuma_dati["running_progress"]
        progresa_josla.progress(progress, text=progresa_text)

        time.sleep(5)
        uzdevuma_dati = dabut_kartes_info()

    st.toast("Karte tika veiksmīgi izveidota.", icon="✅")

    st.session_state.uzdevums_aktivs = False
    st.session_state.ir_karte_izveidota = True

    st.rerun()
