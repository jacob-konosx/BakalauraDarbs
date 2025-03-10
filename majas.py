import requests, time, json
import streamlit as st
from io import BytesIO
from karte import zimet_karti

def savienotWebODM():
    try:
        res = requests.post(f"{st.secrets.webodm_url}/api/token-auth/",
                    data={'username': st.secrets.webodm_username,
                        'password': st.secrets.webodm_password}).json()

        if "token" in res:
            return res['token']
        else:
            return None
    except requests.exceptions.RequestException:
        return None

if "token" not in st.session_state:
    st.session_state.tif = None
    st.session_state.token = savienotWebODM()
    st.session_state.uploader_key = 0
    st.session_state.toast_paradits = False
    st.session_state.task_id = None
    st.session_state.task_progresa = None


if st.session_state.token:
    if not st.session_state.toast_paradits:
        st.toast("WebODM savienots veiksmīgi.", icon="✅")
        st.session_state.toast_paradits = True
else:
    st.toast("WebODM neizdevās savienot.", icon="🚨")

    if st.button("Vēlreiz savienot ar WebODM", icon="🔄"):
        st.session_state.token = savienotWebODM()
    st.stop()

HEADERS = {'Authorization': f"JWT {st.session_state.token}"}

st.title("Dronu un sensoru datu ĢIS")

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

if st.session_state.tif:
    zimet_karti(st.session_state.tif)

    col1, col2 = st.columns([4, 0.4])

    with col1:
        st.download_button(
            label="Lejuplādēt GeoTIFF ortofoto",
            data=st.session_state.tif,
            file_name="ortofoto.tif",
            mime="image/tiff",
            icon="📥"
        )
    with col2:
        if st.button("❌"):
            st.session_state.task_id = None
            st.session_state.tif = None
            st.rerun()

faili = st.file_uploader("Izvēlieties failus:", type=["jpg"], accept_multiple_files=True, key=st.session_state.uploader_key)

if faili:
    if st.button("📤 Ģenerēt karti"):
        if not faili:
            st.error("⚠️ Lūdzu augšupielādējiet vismaz vienu attēlu!")
        else:

            atteli = [("images", (fails.name, fails.getvalue(), fails.type)) for fails in faili]
            options = json.dumps([
                {'name': "orthophoto-resolution", 'value': 24}
            ])

            res = requests.post(f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/",
                    headers=HEADERS,
                    files=atteli,
                    data={
                        'options': options
                    }
                )

            data = res.json()

            if res.status_code == 201:
                st.toast("Attēli veiksmīgi augšupielādēti WebODM.", icon="📤")

                st.session_state.task_id = data["id"]
                st.session_state.task_progresa = True
            else:
                st.toast(f"❌ Kļūda failu augšuplādē: {res.status_code}")
        faili = None

if st.session_state.task_progresa:
    progresa_text = "Notiek kartes izveidošana. Lūdzu uzgaidiet."

    progresa_josla = st.progress(0, text=progresa_text)
    while True:
        task = requests.get(f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/{st.session_state.task_id}/",
            headers=HEADERS).json()
        progress = task['running_progress']

        progresa_josla.progress(progress, text=progresa_text)

        if task['status'] == 40:
            st.toast("Karte tika veiksmīgi ģenerēta.", icon="✅")
            break
        time.sleep(5)

    time.sleep(1)
    progresa_josla.empty()

    # Download the stitched GeoTIFF
    orthophoto_url = f"{st.secrets.webodm_url}/api/projects/{st.secrets.webodm_project_id}/tasks/{st.session_state.task_id}/download/orthophoto.tif"

    tif_res = requests.get(orthophoto_url, stream=True, headers=HEADERS)
    tif_res.raise_for_status()

    st.session_state.tif = BytesIO(tif_res.content)

    st.session_state.task_progresa = False
    st.session_state.uploader_key += 1
    st.rerun()
