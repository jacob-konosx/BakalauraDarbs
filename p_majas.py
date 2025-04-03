import requests, time, json
import streamlit as st
from io import BytesIO

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

def savienot_web_odm():
    try:
        res = requests.post(
            f"{st.secrets.webodm_url}/api/token-auth/",
            data={
                'username': st.secrets.webodm_username,
                'password': st.secrets.webodm_password
            }
        ).json()

        if "token" in res:
            st.session_state.galvene = {'Authorization': f"JWT {res['token']}"}
    except requests.exceptions.RequestException:
        st.toast("Kļūda ietsatot WebODM talonu.", icon="⚠️")

if "galvene" not in st.session_state:
    st.session_state.tif = None
    st.session_state.galvene = None
    st.session_state.uploader_key = 0
    st.session_state.toast_paradits = False
    st.session_state.task_id = None
    st.session_state.task_progresa = None

if not st.session_state.galvene:
    savienot_web_odm()

if st.session_state.galvene:
    if not st.session_state.toast_paradits:
        st.toast("WebODM savienots veiksmīgi.", icon="✅")
        st.session_state.toast_paradits = True
else:
    st.toast("WebODM neizdevās savienot. Lūdzu mēģiniet vēlreiz", icon="🚨")

    st.warning("Bezpilota gaisa kuģu attēlu sašūšanu nodrošina WebODM API.")
    if st.button("Savienot ar WebODM", icon="🔄"):
        st.session_state.web_odm_talons = savienot_web_odm()
    st.stop()

st.title("Dronu un sensoru datu ĢIS")

faili = None
if st.session_state.tif:
    col1, col2 = st.columns([5, 0.4])

    with col1:
        st.download_button(
            label="Lejuplādēt sašūto GeoTIFF ortofoto",
            data=st.session_state.tif,
            file_name="ortofoto.tif",
            mime="image/tiff",
            icon="📥"
        )
    with col2:
        st.button("❌", on_click=lambda: st.session_state.update({"task_id": None, "tif": None}))
else:
    faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)

if faili:
    if st.button("📤 Ģenerēt karti"):
        atteli = [("images", (fails.name, fails.getvalue(), fails.type)) for fails in faili]
        web_odm_iestatijumi = json.dumps([
            {'name': "sfm-algorithm", 'value': "planar"},
            {'name': "fast-orthophoto", 'value': True},
            {'name': "matcher-neighbors", 'value': 4},
            {'name': "pc-quality", 'value': "high"},
            {'name': "orthophoto-resolution", 'value': "2.0"}
        ])

        res = requests.post(f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/",
                headers=st.session_state.galvene,
                files=atteli,
                data={
                    'options': web_odm_iestatijumi
                }
            )

        data = res.json()

        if res.status_code == 201:
            st.toast("Attēli veiksmīgi augšupielādēti WebODM.", icon="📤")

            st.session_state.task_id = data["id"]
            st.session_state.task_progresa = True
        else:
            st.toast(f"Kļūda failu augšuplādē: {res.status_code}", icon="❌")

if st.session_state.task_progresa:
    progresa_text = "Notiek kartes izveidošana. Lūdzu uzgaidiet."

    progresa_josla = st.progress(0, text=progresa_text)
    while True:
        task = requests.get(f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/{st.session_state.task_id}/",
            headers=st.session_state.galvene
        ).json()

        if "running_progress" in task:
            if task['status'] == 40:
                st.toast("Karte tika veiksmīgi sašūta.", icon="✅")
                break

            progress = task["running_progress"]

            progresa_josla.progress(progress, text=progresa_text)
            time.sleep(5)
        else:
            st.toast("Neizdevās dabūt WebODM task progresu.", icon="⚠️")

    progresa_josla.empty()

    orthophoto_url = f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/{st.session_state.task_id}/download/orthophoto.tif"

    tif_res = requests.get(orthophoto_url, stream=True, headers=st.session_state.galvene)
    tif_res.raise_for_status()

    st.session_state.tif = BytesIO(tif_res.content)

    st.session_state.task_progresa = False
    st.session_state.uploader_key += 1
    st.rerun()
