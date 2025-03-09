import streamlit as st
from karte import zimet_karti

if "tif_uploader_key" not in st.session_state:
    st.session_state.tif_uploader_key = 1

st.markdown(
    """
    <style>
        div[data-testid="stFileUploaderDropzoneInstructions"] div span, small {
            display: none;
        }

        div[data-testid="stFileUploaderDropzoneInstructions"] div::after {
            content: "Izvēlēties TIF failu (200MB faila limits)";
        }

        section[data-testid="stFileUploaderDropzone"]{
            cursor: pointer;
        }

        div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="stBaseButton-secondary"] {
            display: none;
        }
    <style>
    """, unsafe_allow_html=True)

st.title("Apskatīt TIF failu")

tif_fails = st.file_uploader("Izvēlieties failu:", type=["tif"], accept_multiple_files=False, key=st.session_state.tif_uploader_key)

if tif_fails:
    zimet_karti(tif_fails)
