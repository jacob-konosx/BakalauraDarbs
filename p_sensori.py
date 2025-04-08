import datetime
import streamlit as st
from dati import dabut_visus_sensora_ierakstus, zimet_sensora_datus

if "sensora_dati" not in st.session_state:
    st.session_state.sensora_dati = None

diapzonas_sakums = datetime.date(2023, 7, 23)
st.date_input("Ievadiet sensoru datu datuma diapzonu:", format="DD.MM.YYYY", key="datuma_diapzona", value=[diapzonas_sakums, diapzonas_sakums + datetime.timedelta(days=3)])

if len(st.session_state.datuma_diapzona) == 2:
    sensora_dati = dabut_visus_sensora_ierakstus(st.session_state.datuma_diapzona)

    if sensora_dati:
        if len(sensora_dati) > 0:
            st.session_state.sensora_dati = sensora_dati
        else:
            st.warning(f"Sensora dati nav pieejami datuma diapzonā: {st.session_state.datuma_diapzona[0].strftime('%d.%m.%Y')} - {st.session_state.datuma_diapzona[1].strftime('%d.%m.%Y')}")
    else:
        st.toast("Neizdevās pieprasīt sensora datus.", icon="⚠️")

if st.session_state.sensora_dati:
    zimet_sensora_datus(st.session_state.sensora_dati)
