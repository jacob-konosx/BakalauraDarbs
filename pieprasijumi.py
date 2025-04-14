import requests, json
import streamlit as st

odm_iestatijumi = json.dumps([
    {'name': "sfm-algorithm", 'value': "planar"},
    {'name': "fast-orthophoto", 'value': True},
    {'name': "matcher-neighbors", 'value': 4},
    {'name': "pc-quality", 'value': "high"},
    {'name': "orthophoto-resolution", 'value': "2.0"}
])

def savienot_odm():
    try:
        atb = requests.post(
            f"{st.secrets.odm_url}/token-auth/",
            data={
                'username': st.secrets.odm_username,
                'password': st.secrets.odm_password
            }
        )
        atb.raise_for_status()

        st.toast("ODM savienots veiksmīgi.", icon="✅")
        return json.dumps({"Authorization": f"JWT {atb.json()['token']}"})
    except:
        st.toast("Kļūda ietsatot ODM talonu!", icon="🚨")

def atcelt_uzdevumu():
    try:
        atb = requests.post(f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{st.session_state.uzdevuma_id}/remove/", headers=st.session_state.galvene)
        atb.raise_for_status()

        st.session_state.uzdevuma_id = None
        st.session_state.uzdevums_aktivs = False
    except:
        st.toast("Neizdevās atcelt uzdevumu!", icon="🚨")

def izveidot_uzdevumu(atteli, kartes_nosaukums):
    try:
        atb = requests.post(f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/",
                headers=st.session_state.galvene,
                files=atteli,
                data={
                    "options": odm_iestatijumi,
                    "name": kartes_nosaukums
                }
            )
        atb.raise_for_status()

        st.session_state.uzdevuma_id = atb.json()["id"]
        st.session_state.uzdevums_aktivs = True
        st.session_state.uploader_key += 1

        st.toast("Attēli veiksmīgi augšupielādēti ODM.", icon="📤")
    except:
        st.toast("Kļūda failu augšuplādē!", icon="🚨")

def dabut_uzdevuma_info():
    try:
        atb = requests.get(f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{st.session_state.uzdevuma_id}",
                headers=st.session_state.galvene
            )
        atb.raise_for_status()

        return atb.json()
    except:
        st.toast("Neizdevās dabūt uzdevuma info!", icon="🚨")

@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_sensora_datus(sensora_datu_url):
    try:
        atb = requests.get(sensora_datu_url)
        atb.raise_for_status()

        return atb.json()
    except:
        return None

@st.cache_data
def lejupladet_tif(uzdevuma_id):
    lejuplades_url = f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{uzdevuma_id}/download/orthophoto.tif"

    try:
        atb = requests.get(lejuplades_url, stream=True, headers=st.session_state.galvene)
        atb.raise_for_status()

        return atb.content
    except:
        st.toast("Neizdevās lejuplādēt uzdevumu!", icon="🚨")

def izveidot_projektu():
    try:
        atb = requests.post(f"{st.secrets.odm_url}/projects/",
                headers=st.session_state.galvene,
                data={
                    "name": st.experimental_user.email,
                }
            )
        atb.raise_for_status()

        return atb.json()
    except:
        st.toast("Neizdevās izveidot projektu!", icon="🚨")
