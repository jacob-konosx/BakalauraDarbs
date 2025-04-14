import streamlit as st
from pieprasijumi import izveidot_projektu
from db import dabut_lietotaju_pec_epasta, vai_pilnvarots_epasts, izveidot_lietotaju

def iestatit_lietotaju():
    projekta_id = None

    db_lietotajs = dabut_lietotaju_pec_epasta()
    if not db_lietotajs:
        if vai_pilnvarots_epasts():
            izveidotais_projekts = izveidot_projektu()

            if izveidotais_projekts:
                projekta_id = izveidotais_projekts["id"]
                izveidot_lietotaju(projekta_id)
        else:
            st.info("Jūsu e-pasta adrese nav pilnvarota sitēmā. Sazinaties ar tīmekļa lietotnes administratoru, lai pilnvarotu Jūsu e-pasta adresi.", icon="ℹ️")

            st.button("Mēģiniet vēlreiz autentificēties", icon="🔐", on_click=st.logout)
            st.stop()
    else:
        projekta_id = db_lietotajs["projekta_id"]

    return str(projekta_id)
