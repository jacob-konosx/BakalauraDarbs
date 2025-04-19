import datetime
from streamlit_folium import st_folium, folium_static
import streamlit as st
from io import BytesIO
from dati import zimet_sensora_datus, dabut_visus_sensora_ierakstus, ieladet_sensora_datus
from pieprasijumi import dabut_lietotaja_kartes, lejupladet_karti_pec_id, izdzest_karti_pec_id
from karte import izveidot_karti

KARTES_AUGSTUMS = 600

def uzstadit_state():
    st.session_state.tif_fails = None
    st.session_state.tif_datums = None
    st.session_state.tif_laiks = datetime.time(0, 0)
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.tif_sensora_dati = None
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
    st.session_state.tif_laiks = datetime.time(0, 0)
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.ierices = {}
    st.session_state.tif_sensora_dati = None

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

@st.dialog("Izvēlaties sensora datu datumu")
def izveleties_karti(kartes_id):
    tif_fails =  BytesIO(lejupladet_karti_pec_id(kartes_id))
    izveletais_datums = st.date_input("Izvēlaties GeoTIFF datumu:", format="DD.MM.YYYY", value=None)

    if st.button("Apsiprināt datus", disabled=izveletais_datums==None or tif_fails==None, icon="✔️"):
        st.session_state.tif_datums = izveletais_datums
        st.session_state.tif_fails = tif_fails
        st.session_state.kartes_id = kartes_id
        st.rerun()

@st.dialog("Izvēlaties GeoTIFF kartes failu")
def izvēlēties_failu():
    izveletais_datums = st.date_input("Izvēlaties bildes uzņemšanas datumu:", format="DD.MM.YYYY", value=None)
    tif_fails = st.file_uploader("Izvēlieties GeoTIFF failu:", type=["tif"], accept_multiple_files=False)
    if st.button("Apsiprināt datus", disabled=izveletais_datums==None or tif_fails==None, icon="✔️"):
        st.session_state.tif_fails = tif_fails
        st.session_state.tif_datums = izveletais_datums
        st.rerun()

@st.dialog("Lejuplādēt GeoTIFF karti")
def lejupladet_karti(kartes_id, nosaukums):
    st.header(f"Karte: {nosaukums}")
    kartes_fails = lejupladet_karti_pec_id(kartes_id)

    if kartes_fails:
        st.download_button(
            label="Lejuplādēt GeoTIFF failu",
            data=kartes_fails,
            file_name=f"{nosaukums}.tif",
            mime="image/tiff",
            icon="💾"
        )

@st.dialog("Vai Jūs tiešām vēlaties dzēst karti?")
def izdzest_karti(kartes_id):
    if st.button("Dzēst karti", icon="🗑️"):
        izdzest_karti_pec_id(kartes_id)
        st.session_state.kartes =  None
        st.rerun()

st.title("GeoTIFF Kartes")
if st.session_state.tif_fails:
    if not st.session_state.tif_sensora_dati:
        dienas_diapzona = [st.session_state.tif_datums, st.session_state.tif_datums + datetime.timedelta(days=1)]
        st.session_state.tif_sensora_dati = dabut_visus_sensora_ierakstus(dienas_diapzona)

        if st.session_state.tif_sensora_dati:
            st.session_state.ierices = ieladet_sensora_datus(st.session_state.tif_sensora_dati)

    cilne1, cilne2 = st.tabs(["Karte", "Sensora dati"])

    with cilne1:
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
            st.button("❌", on_click=uzstadit_state, help="Aizvērt karti")

        kartes_konteineris = st.container()

        bez_koordinatas_ierices = [ierices_id for ierices_id, ierices_dati in st.session_state.ierices.items() if not ierices_dati["koordinatas"]]
        if len(bez_koordinatas_ierices) > 0:
            st.info(f"Nepieciešams izvēlēties koordinātas {len(bez_koordinatas_ierices)} ierīcēm: {', '.join(bez_koordinatas_ierices)}.")
            izveleta_ierice = st.selectbox("Izvēlies ierīci, kurai uzstādīt koordinātas:", bez_koordinatas_ierices)

            if not st.session_state.spiediena_rezims:
                st.button("Izvēlēties koordinātas", icon="🗺️", on_click=lambda: st.session_state.update(spiediena_rezims=True))
            else:
                st.button("Apstiprināt koordinātas", icon="💾", on_click=apstiprinat_koordinatu, args=(izveleta_ierice, ))

        with kartes_konteineris:
                renderet_karti()
    with cilne2:
        if st.session_state.tif_sensora_dati:
            st.subheader(f"Sensora dati datumā: {st.session_state.tif_datums}")
            zimet_sensora_datus(st.session_state.tif_sensora_dati)
        else:
            st.info(f"Sensora dati nav pieejami {st.session_state.tif_datums.strftime('%d.%m.%Y')}. Lūdzu izvēlaties citu datumu!", icon="ℹ️")
else:
    col1, col2, col3 = st.columns([1.5, 2.5, 1.5])
    with col1:
        st.button("Atjaunināt kartes sarakstu", on_click=lambda: st.session_state.update(kartes=dabut_lietotaja_kartes()), icon="🔄")
    with col3:
        st.button("Atvērt karti no GeoTIFF failu", icon="📂", on_click=izvēlēties_failu)
    if not st.session_state.kartes:
        st.session_state.kartes = dabut_lietotaja_kartes()

    if len(st.session_state.kartes) > 0:
        for i, karte in enumerate(st.session_state.kartes):
            with st.container(border=True):
                dt = datetime.datetime.strptime(karte["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
                kartes_id = karte["id"]

                col1, col2, col3, col4, col5 = st.columns([5, 2, 1.3, 0.8, 0.8])
                with col1:
                    st.text(f"{i+1} . {karte['name']}")
                with col2:
                    st.text(dt.strftime("%d.%m.%Y %H:%M"))
                with col3:
                    if st.button(f"Skatīt", key="izvele_"+kartes_id, disabled=not karte["status"]==40, icon="🗺️", help="Atvērt GeoTIFF karti" if karte["status"]==40 else "Karte tiek izveidota"):
                        izveleties_karti(kartes_id)
                with col4:
                    st.button("💾", key="lejup_"+kartes_id, on_click=lejupladet_karti, args=(kartes_id, karte["name"]), help="Saglabāt GeoTIFF karti")
                with col5:
                    st.button("🗑️", key="dzest_"+kartes_id, on_click=izdzest_karti, args=(kartes_id,), help="Dzēst GeoTIFF karti")
    else:
        st.info('Sistēmā netika atrasta neviena karte. Lai izveidotu karti, dodaties uz "Kartes Izveide" lapu.')
