import requests, json
import streamlit as st
from requests.exceptions import HTTPError

ODM_IESTATIJUMI = json.dumps([
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
        elif e.response.status_code == 404:
            return None
        else:
            st.error(f"Kļūda pieprasījumā: {e}")

def izdzest_karti_pec_id(kartes_id):
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{kartes_id}/remove/")

    if atb:
        return atb.json()

def izveidot_karti(atteli, kartes_nosaukums):
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/",
            faili=atteli,
            dati={
                "options": ODM_IESTATIJUMI,
                "name": kartes_nosaukums
            }
        )
    if atb:
        return atb.json()

def dabut_kartes_info_pec_id(kartes_id):
    atb = pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{kartes_id}")

    if atb:
        return atb.json()

@st.cache_data(show_spinner="Lejuplādē karti")
def lejupladet_karti_pec_id(kartes_id):
    lejuplades_url = f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{kartes_id}/download/orthophoto.tif"

    atb = pieprasit_odm("GET", lejuplades_url, stream=True)

    if atb:
        return atb.content

def izveidot_projektu():
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/",
            dati={
                "name": st.experimental_user.email,
            }
        )

    if atb:
        return atb.json()

def dabut_lietotaja_kartes():
    atb = pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/",)

    if atb:
        return atb.json()
