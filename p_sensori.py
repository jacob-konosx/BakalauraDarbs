import datetime
import streamlit as st
from dati import dabut_sensora_datus, dabut_visus_items, dabut_str_diapzonu, zimet_sensora_datus

if "sensora_dati" not in st.session_state:
    st.session_state.sensora_dati = None

diapzonas_sakums = datetime.date(2023, 7, 23)
st.date_input("Ievadiet sensoru datu datuma diapzonu:", format="DD.MM.YYYY", key="datuma_diapzona", value=[diapzonas_sakums, diapzonas_sakums + datetime.timedelta(days=3)])

if len(st.session_state.datuma_diapzona) == 2:
    str_diapzona = dabut_str_diapzonu([st.session_state.datuma_diapzona[0], st.session_state.datuma_diapzona[1]])
    sensora_dati = dabut_sensora_datus(st.secrets.sensoru_datu_url.format(str_diapzona[0], str_diapzona[1]))

    if sensora_dati:
        if len(sensora_dati["items"]) > 0:
            st.session_state.sensora_dati = sensora_dati["items"]

            if sensora_dati["hasMore"]:
                st.session_state.sensora_dati += dabut_visus_items(sensora_dati)
        else:
            st.warning(f"Sensora dati nav pieejami datuma diapzonā: {st.session_state.datuma_diapzona[0].strftime('%d.%m.%Y')} - {st.session_state.datuma_diapzona[1].strftime('%d.%m.%Y')}")
    else:
        st.toast("Neizdevās pieprasīt sensora datus.", icon="⚠️")

if st.session_state.sensora_dati:
    zimet_sensora_datus(st.session_state.sensora_dati)
