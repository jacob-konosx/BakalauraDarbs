import time
import streamlit as st
from pieprasijumi import lejupladet_tif, dabut_uzdevuma_info, izveidot_uzdevumu, savienot_odm, atcelt_uzdevumu

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

if "tif" not in st.session_state:
    st.session_state.tif = None
    st.session_state.uploader_key = 0
    st.session_state.toast_paradits = False
    st.session_state.uzdevuma_id = None
    st.session_state.uzdevums_aktivs = False

def generet_karti(faili):
    atteli = [("images", (fails.name, fails.getvalue(), fails.type)) for fails in faili]
    izveidot_uzdevumu(atteli)

if not st.session_state.galvene:
    savienot_odm()

if st.session_state.galvene:
    if not st.session_state.toast_paradits:
        st.toast("ODM savienots veiksmīgi.", icon="✅")
        st.session_state.toast_paradits = True
else:
    st.toast("ODM neizdevās savienot. Lūdzu mēģiniet vēlreiz", icon="🚨")

    st.warning("Bezpilota gaisa kuģu attēlu sašūšanu nodrošina ODM API.")
    st.button("Savienot ar ODM", icon="🔄", on_click=savienot_odm)
    st.stop()

st.title("Dronu un sensoru datu ĢIS")

izveleti_faili = None
if not st.session_state.uzdevums_aktivs:
    if st.session_state.tif:
        col1, col2 = st.columns([5, 0.4])

        with col1:
            st.subheader("Ortofoto ir gatavs lejuplādei.")
            st.download_button(
                label="Lejuplādēt sašūto GeoTIFF ortofoto",
                data=st.session_state.tif,
                file_name="ortofoto.tif",
                mime="image/tiff",
                icon="📥"
            )
        with col2:
            st.button("❌", on_click=lambda: st.session_state.update({"uzdevuma_id": None, "tif": None}), help="")
    else:
        izveleti_faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)

    if izveleti_faili:
        st.button("📤 Ģenerēt karti", on_click=generet_karti, args=(izveleti_faili,))
else:
    progresa_text = "Notiek kartes izveidošana. Lūdzu uzgaidiet."
    col1, col2 = st.columns([5, 1.5])

    with col1:
        progresa_josla = st.progress(0, text=progresa_text)
    with col2:
        st.button("Atcelt kartes izveidi", on_click=atcelt_uzdevumu, icon="❌")

    while True:
        uzdevuma_dati = dabut_uzdevuma_info()

        if uzdevuma_dati:
            if uzdevuma_dati['status'] == 40:
                st.toast("Karte tika veiksmīgi sašūta.", icon="✅")
                break

            progress = uzdevuma_dati["running_progress"]

            progresa_josla.progress(progress, text=progresa_text)
            time.sleep(5)

    progresa_josla.empty()

    lejupladet_tif()
    st.rerun()
