import requests, json
import streamlit as st
from requests.exceptions import HTTPError

ODM_IESTATIJUMI = [
    {'name': "sfm-algorithm", 'value': "planar"},
    {'name': "fast-orthophoto", 'value': True},
    {'name': "matcher-neighbors", 'value': 4},
    {'name': "tiles", 'value': True}
]

@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_sensora_datus(sensora_datu_url):
    try:
        atb = requests.get(sensora_datu_url)
        atb.raise_for_status()

        return atb.json()
    except Exception as e:
        st.error(f"Neizdevās dabūt sensora datus: {e}")

def iestatit_galveni():
    try:
        atb = requests.post(
            f"{st.secrets.odm_url}/token-auth/",
            data={
                'username': st.secrets.odm_username,
                'password': st.secrets.odm_password
            }
        )
        atb.raise_for_status()
        rez = atb.json()

        if rez["token"]:
            st.session_state.sikdatne["galvene"] = json.dumps({"Authorization": f"JWT {rez['token']}"})
            return True
    except Exception as e:
        st.error("Kļūda WebODM savienojumā")

def pieprasit_odm(metode, url, dati=None, faili=None, stream=False, meginajumi=0):
    meginajumi += 1
    if meginajumi == 5:
        st.error("Neizdevās atkārtoti iestatīt WebODM JWT žetonu.")

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
            ir_galvene_iestatita = iestatit_galveni()

            if ir_galvene_iestatita:
                if metode == "GET":
                    return pieprasit_odm("GET", url, stream=stream, meginajumi=meginajumi)
                elif metode == "POST":
                    return pieprasit_odm("POST", url, dati=dati, faili=faili, meginajumi=meginajumi)
            else:
                st.error("Atkārtotā WebODM pieprasījumā neizdevās iestatīt JWT žetonu.")
        else:
            st.error(f"Kļūda pieprasījumā: {e}")

def dabut_uzdevuma_info_pec_id(kartes_id):
    atb = pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{kartes_id}")

    if atb:
        return atb.json()

@st.cache_data(show_spinner="Lejuplādē karti")
def lejupladet_tif_pec_id(kartes_id):
    lejuplades_url = f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{kartes_id}/download/orthophoto.tif"

    atb = pieprasit_odm("GET", lejuplades_url, stream=True)

    if atb:
        return atb.content

def dabut_lietotaja_uzdevumus():
    atb = pieprasit_odm("GET", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/",)

    if atb:
        return atb.json()

def izveidot_karti(kartes_nosaukums, ortofoto_izskirtspeja):
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/",
            dati={
                "options": json.dumps([{'name': "orthophoto-resolution", 'value': ortofoto_izskirtspeja}, *ODM_IESTATIJUMI]),
                "name": kartes_nosaukums,
                "partial": True
            }
        )
    if atb:
        return atb.json()

def izdzest_uzdevumu_pec_id(uzdevuma_id):
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{uzdevuma_id}/remove/")

    if atb:
        return atb.json()

def augsupieladet_odm_attelus_pec_id(uzdevuma_id, atteli):
    pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{uzdevuma_id}/upload/",
        faili=atteli
    )

def sakt_uzdevumu_pec_id(uzdevuma_id):
    pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{uzdevuma_id}/commit/")

def izveidot_projektu():
    atb = pieprasit_odm("POST", f"{st.secrets.odm_url}/projects/",
            dati={
                "name": st.user.email,
            }
        )

    if atb:
        return atb.json()
