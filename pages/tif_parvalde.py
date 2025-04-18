import datetime
from streamlit_folium import st_folium, folium_static
import streamlit as st
from io import BytesIO
from dati import zimet_sensora_datus, dabut_visus_sensora_ierakstus, ieladet_sensora_datus
from pieprasijumi import dabut_lietotaja_kartes, lejupladet_karti_pec_id, izdzest_karti_pec_id
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

        .stText{
            padding: 0.4rem 0px;
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
    st.session_state.kartes = None
    st.session_state.kartes_id = None

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

if "kartes" not in st.session_state:
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

@st.dialog("Izvlaties senosra datu datumu")
def izveleties_karti(kartes_id):
    st.session_state.tif_fails =  BytesIO(lejupladet_karti_pec_id(kartes_id))
    izveletais_datums = st.date_input("Izvēlaties bildes uzņemšanas datumu:", format="DD.MM.YYYY", value=None)

    if st.button("Apsiprināt datus", disabled=izveletais_datums==None, icon="✔️"):
        st.session_state.tif_datums = izveletais_datums
        st.session_state.kartes_id = kartes_id
        st.rerun()

def izdzest_karti(kartes_id):
    izdzest_karti_pec_id(kartes_id)
    st.session_state.kartes =  None

st.title("GeoTIFF Kartes")

if st.session_state.tif_fails:
    dienas_diapzona = [st.session_state.tif_datums, st.session_state.tif_datums + datetime.timedelta(days=1)]
    st.session_state.tif_sensora_dati = dabut_visus_sensora_ierakstus(dienas_diapzona)

    if st.session_state.tif_sensora_dati:
        st.session_state.ierices = ieladet_sensora_datus(st.session_state.tif_sensora_dati)

    col1, col2, col3, col4 = st.columns([3, 3, 8, 1])
    with col1:
        izveletais_datums = st.date_input("Sensora datu datums:", format="DD.MM.YYYY", value=st.session_state.tif_datums)

        if not izveletais_datums == st.session_state.tif_datums:
            st.session_state.tif_datums = izveletais_datums
            tif_datuma_izmaina()
            st.rerun()
    with col2:
        izveletais_laiks = st.time_input("Sensora datu laiks:", value=st.session_state.tif_laiks)

        if not izveletais_laiks == st.session_state.tif_laiks:
            st.session_state.tif_laiks = izveletais_laiks
            st.rerun()
    with col4:
        st.button("❌", on_click=uzstadit_state)

    kartes_konteineris = st.container()

    bez_koordinatas_ierices = [ierices_id for ierices_id, ierices_dati in st.session_state.ierices.items() if not ierices_dati["koordinatas"]]
    if len(bez_koordinatas_ierices) > 0:
        st.info(f"Nepieciešams izvēlēties koordinātas {len(bez_koordinatas_ierices)} ierīcēm: {', '.join(bez_koordinatas_ierices)}.")
        izveleta_ierice = st.selectbox("Izvēlies ierīci, kurai uzstādīt koordinātas:", bez_koordinatas_ierices)

        if not st.session_state.spiediena_rezims:
            st.button("Izvēlēties koordinātas", icon="🗺️", on_click=lambda: st.session_state.update(spiediena_rezims=True))
        else:
            st.button("Apstiprināt koordinātas", icon="💾", on_click=apstiprinat_koordinatu, args=(izveleta_ierice, ))

    if st.session_state.tif_sensora_dati:
        st.subheader(f"Sensora dati datumā: {st.session_state.tif_datums}")
        zimet_sensora_datus(st.session_state.tif_sensora_dati)

    with kartes_konteineris:
        renderet_karti()
else:
    st.button("Atjaunināt kartes sarakstu", on_click=lambda: st.session_state.update(kartes=dabut_lietotaja_kartes()), icon="🔄")
    if not st.session_state.kartes:
        st.session_state.kartes = dabut_lietotaja_kartes()

    if len(st.session_state.kartes) > 0:
        for i, karte in enumerate(st.session_state.kartes):
            with st.container(border=True):
                dt = datetime.datetime.strptime(karte["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
                kartes_id = karte["id"]

                col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
                with col1:
                    st.text(f"{i+1} . {karte['name']}")
                with col2:
                    st.text(dt.strftime("%d.%m.%Y %H:%M"))
                with col3:
                    if st.button(f"Atvērt", key="izvele_"+kartes_id, disabled=not karte["status"]==40, icon="🗺️", help="Atvērt GeoTIFF karti" if karte["status"]==40 else "Karte tiek izveidota"):
                        izveleties_karti(kartes_id)
                with col4:
                    st.button("Dzēst", icon="❌", key=kartes_id, on_click=izdzest_karti, args=(kartes_id,))
    else:
        st.info('Sistēmā netika atrasta neviena karte. Lai izveidotu karti, dodaties uz "Kartes Izveide" lapu.')
