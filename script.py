import streamlit as st

if "ierakstijies" not in st.session_state:
    st.session_state.ierakstijies = False

majas = st.Page("majas.py", title="Mājas")
tif_lapa = st.Page("tifs.py", title="Apskatīt TIF")

pg = st.navigation([majas, tif_lapa])

pg.run()
