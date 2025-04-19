import requests, json
import streamlit as st
from requests.exceptions import HTTPError

odm_iestatijumi = json.dumps([
    {'name': "sfm-algorithm", 'value': "planar"},
    {'name': "fast-orthophoto", 'value': True},
    {'name': "matcher-neighbors", 'value': 4},
    {'name': "pc-quality", 'value': "high"},
    {'name': "orthophoto-resolution", 'value': "2.0"}
])

@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_sensora_datus(sensora_datu_url):
    try:
        atb = requests.get(sensora_datu_url)
        atb.raise_for_status()

        return atb.json()
    except Exception as e:
        st.error(f"Neizdevās dabūt sensora datus: {e}")

def dabut_galveni():
    try:
        atb = requests.post(
            f"{st.secrets.odm_url}/token-auth/",
            data={
                'username': st.secrets.odm_username,
                'password': st.secrets.odm_password
            }
        )
        atb.raise_for_status()

        return {"Authorization": f"JWT {atb.json()['token']}"}
    except Exception as e:
        st.error(f"Kļūda ODM savienojumā: {e}")

def pieprasit_odm(metode, url, dati=None, faili=None, stream=False):
    galvene = json.loads(st.session_state.sikdatne["galvene"])

    try:
        if metode == "GET":
            atb = requests.get(url, headers=galvene, stream=stream)
        elif metode == "POST":
            atb = requests.post(url, headers=galvene, data=dati, files=faili)
        else:
            raise ValueError("Neatbalstīta metode")

        atb.raise_for_status()
        return atb

    except HTTPError as e:
        if e.response.status_code == 403:
            galvene = dabut_galveni()
            st.session_state.sikdatne["galvene"] = json.dumps(galvene)

            if metode == "GET":
                return requests.get(url, headers=galvene, stream=stream)
            elif metode == "POST":
                return requests.post(url, headers=galvene, data=dati, files=faili)
        else:
            st.error(f"Kļūda pieprasījumā: {e}")

def izdzest_karti_pec_id(kartes_id):
    pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{kartes_id}/remove/")

def izveidot_karti(atteli, kartes_nosaukums):
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/",
            faili=atteli,
            dati={
                "options": odm_iestatijumi,
                "name": kartes_nosaukums
            }
        )
    dati = atb.json()

    if dati:
        st.session_state.uzdevuma_id = dati["id"]
        st.session_state.uzdevums_aktivs = True
        st.session_state.uploader_key += 1

        return True

def dabut_kartes_info():
    return pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{st.session_state.uzdevuma_id}").json()

@st.cache_data(show_spinner="Lejuplādē karti")
def lejupladet_karti_pec_id(kartes_id):
    lejuplades_url = f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{kartes_id}/download/orthophoto.tif"

    atb = pieprasit_odm("GET", lejuplades_url, stream=True)

    return atb.content

def izveidot_projektu():
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/",
            dati={
                "name": st.experimental_user.email,
            }
        )

    return atb.json()

def dabut_lietotaja_kartes():
    atb = pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/",)

    return atb.json()
