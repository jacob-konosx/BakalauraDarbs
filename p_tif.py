import datetime
from streamlit_folium import st_folium, folium_static
import streamlit as st
from dati import zimet_sensora_datus, dabut_visus_sensora_ierakstus, ieladet_sensora_datus
from karte import izveidot_karti

st.markdown(
    """
    <style>
        div[data-testid="stFileUploaderDropzoneInstructions"] div span, small {
            display: none;
        }

        div[data-testid="stFileUploaderDropzoneInstructions"] div::after {
            content: "Izvēlēties TIF failu (200MB faila limits)";
        }

        section[data-testid="stFileUploaderDropzone"]{
            cursor: pointer;
        }

        div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="stBaseButton-secondary"] {
            display: none;
        }

        .map-container {
            width: 100%;
        }
    <style>
    """, unsafe_allow_html=True)

KARTES_AUGSTUMS = 600

def uzstadit_state():
    st.session_state.tif_fails = None
    st.session_state.tif_datums = None
    st.session_state.tif_laiks = None
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.tif_sensora_dati = []
    st.session_state.ierices = {}
    st.session_state.datu_slani = []
    st.session_state.kartes_key = 1

def apstiprinat_koordinatu(izveleta_ierice):
    st.session_state.spiediena_rezims = False
    st.session_state.ierices[izveleta_ierice]["koordinatas"] = st.session_state.izveleta_koordinate
    st.session_state.izveleta_koordinate = None

def tif_datuma_izmaina():
    st.session_state.tif_laiks = None
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.ierices = {}
    st.session_state.tif_sensora_dati = []

if "tif_datums" not in st.session_state:
    uzstadit_state()

@st.fragment
def renderet_karti():
    m = izveidot_karti(
        st.session_state.ir_satelita_flizes,
        st.session_state.izveleta_koordinate,
        st.session_state.ierices,
        st.session_state.tif_laiks
    )

    if st.session_state.spiediena_rezims:
        kartes_dati = st_folium(
            m,
            width=None,
            height=KARTES_AUGSTUMS,
            key=st.session_state.kartes_key
        )

        if not st.session_state.izveleta_koordinate:
            st.toast("Izvēlaties koordinātu kartē!", icon="🗺️")

        if kartes_dati.get("last_clicked") :
            lat = kartes_dati["last_clicked"]["lat"]
            lon = kartes_dati["last_clicked"]["lng"]
            st.session_state.izveleta_koordinate = [lat, lon]

            st.rerun(scope="fragment")
    else:
        folium_static(m, width=None, height=KARTES_AUGSTUMS)

st.title("Apstrādāt TIF failu")
if st.session_state.tif_datums:
    dienas_diapzona = [st.session_state.tif_datums, st.session_state.tif_datums + datetime.timedelta(days=1)]
    sensora_dati = dabut_visus_sensora_ierakstus(dienas_diapzona)

    if sensora_dati:
        if len(sensora_dati) > 0:
            st.session_state.tif_sensora_dati = sensora_dati
            ieladet_sensora_datus(st.session_state.tif_sensora_dati)
        else:
            st.warning(f"Sensora dati nav pieejami datuma diapzonā: {dienas_diapzona[0].strftime('%d.%m.%Y')} - {dienas_diapzona[1].strftime('%d.%m.%Y')}")
    else:
        st.error("Neizdevās pieprasīt sensora datus.")


    col1, col2, col3, col4 = st.columns([3, 3, 8, 1])
    with col1:
        st.date_input("Sensora datu datums:", key="tif_datums", format="DD.MM.YYYY", on_change=tif_datuma_izmaina)
    with col2:
        st.time_input("Sensora datu laiks:", key="tif_laiks")
    with col4:
        st.button("❌", on_click=uzstadit_state)

    kartes_konteineris = st.container()

    bez_koordinatas_ierices = [ierices_id for ierices_id, ierices_dati in st.session_state.ierices.items() if not ierices_dati["koordinatas"]]
    if len(bez_koordinatas_ierices) > 0:
        st.warning(f"Nepieciešams izvēlēties koordinātas {len(bez_koordinatas_ierices)} ierīcēm: {', '.join(bez_koordinatas_ierices)}.")
        izveleta_ierice = st.selectbox("Izvēlies ierīci, kurai uzstādīt koordinātas:", bez_koordinatas_ierices)

        if not st.session_state.spiediena_rezims:
            st.button("Izvēlēties koordinātas", icon="🗺️", on_click=lambda: st.session_state.update(spiediena_rezims=True))
        else:
            st.button("Apstiprināt koordinātas", icon="💾", on_click=apstiprinat_koordinatu, args=(izveleta_ierice, ))


    if len(st.session_state.tif_sensora_dati) > 0:
        st.subheader(f"Sensora dati datumā: {st.session_state.tif_datums}")
        zimet_sensora_datus(st.session_state.tif_sensora_dati)

    with kartes_konteineris:
        renderet_karti()
else:
    tif_fails = st.file_uploader("Izvēlieties failu:", type=["tif"], accept_multiple_files=False)
    tif_datums = st.date_input("Izvēlaties bildes uzņemšanas datumu:", value=datetime.date(2023, 7, 23),  format="DD.MM.YYYY")

    if tif_fails and tif_datums:
        st.button("Apstiprināt datus", icon="💾", on_click=lambda: st.session_state.update({"tif_fails": tif_fails, "tif_datums": tif_datums}))
