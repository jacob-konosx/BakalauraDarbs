import datetime
from streamlit_folium import st_folium, folium_static
import streamlit as st
from utils.sensoru_dati import zimet_sensora_datus, dabut_visus_sensora_ierakstus, ieladet_sensora_datus
from utils.pieprasijumi import dabut_lietotaja_uzdevumus, lejupladet_tif_pec_id, izdzest_uzdevumu_pec_id
from utils.db import dabut_odm_uzdevumu_pec_id, atjauninat_odm_uzdevuma_datumu_pec_id, atjauninat_sensora_koordinatas_pec_id, dzest_sensora_koordinatas_pec_uzdevuma_id
from utils.karte import izveidot_karti

KARTES_AUGSTUMS = 600

def uzstadit_state():
    st.session_state.ortofoto_sensora_datums = None
    st.session_state.ortofoto_sensora_laiks = datetime.time(0, 0)
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.ortofoto_sensora_dati = None
    st.session_state.sensora_ierices = {}
    st.session_state.odm_uzdevumi = None
    st.session_state.odm_uzdevums = None
    st.session_state.tif_fails = None

def apstiprinat_koordinatu(izveleta_ierice):
    if st.session_state.odm_uzdevums:
        atjauninat_sensora_koordinatas_pec_id(st.session_state.odm_uzdevums["id"], izveleta_ierice, st.session_state.izveleta_koordinate)

    st.session_state.spiediena_rezims = False
    st.session_state.sensora_ierices[izveleta_ierice]["koordinatas"] = st.session_state.izveleta_koordinate
    st.session_state.izveleta_koordinate = None

def tif_datuma_izmaina():
    st.session_state.ortofoto_sensora_laiks = datetime.time(0, 0)
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.sensora_ierices = {}
    st.session_state.ortofoto_sensora_dati = None

    if st.session_state.odm_uzdevums:
        atjauninat_odm_uzdevuma_datumu_pec_id(st.session_state.odm_uzdevums["id"], st.session_state.ortofoto_sensora_datums)
        dzest_sensora_koordinatas_pec_uzdevuma_id(st.session_state.odm_uzdevums["id"])

if "odm_uzdevumi" not in st.session_state:
    uzstadit_state()

@st.fragment
def renderet_karti():
    m = izveidot_karti(
        st.session_state.izveleta_koordinate,
        st.session_state.sensora_ierices,
        st.session_state.ortofoto_sensora_laiks,
        st.session_state.odm_uzdevums,
        st.session_state.tif_fails
    )

    if st.session_state.spiediena_rezims:
        kartes_dati = st_folium(
            m,
            width=None,
            height=KARTES_AUGSTUMS,
        )

        if kartes_dati.get("last_clicked") :
            lat = kartes_dati["last_clicked"]["lat"]
            lon = kartes_dati["last_clicked"]["lng"]
            st.session_state.izveleta_koordinate = [lat, lon]

            st.rerun(scope="fragment")
    else:
        folium_static(m, width=None, height=KARTES_AUGSTUMS)

def izveleties_karti(odm_uzdevums):
    db_odm_uzdevums = dabut_odm_uzdevumu_pec_id(odm_uzdevums["id"])

    if db_odm_uzdevums:
        st.session_state.ortofoto_sensora_datums = db_odm_uzdevums["datums"]
        st.session_state.odm_uzdevums = odm_uzdevums

@st.dialog("Izvēlaties GeoTIFF kartes failu")
def izvēlēties_failu():
    st.warning("Kartes operācijas ar GeoTIFF failu būs ievērojami lēnākas nekā caur sistēmas kartes izveides procesu!", icon="⚠️")
    st.page_link("lapas/kartes_izveide.py", label="Doties uz kartes izveidi", icon="🪡")

    izveletais_datums = st.date_input("Izvēlaties ortofoto datumu:", format="DD.MM.YYYY", value=None)
    tif_fails = st.file_uploader("Izvēlieties GeoTIFF failu:", type=["tif"], accept_multiple_files=False)

    if st.button("Apsiprināt datus", disabled=izveletais_datums==None or tif_fails==None, icon="✔️"):
        st.session_state.tif_fails = tif_fails
        st.session_state.ortofoto_sensora_datums = izveletais_datums
        st.rerun()

@st.dialog("Lejuplādēt GeoTIFF failu")
def lejupladet_karti(uzdevuma_id, nosaukums):
    st.header(f"Karte: {nosaukums}")
    kartes_fails = lejupladet_tif_pec_id(uzdevuma_id)

    if kartes_fails:
        st.download_button(
            label="Lejuplādēt GeoTIFF failu",
            data=kartes_fails,
            file_name=f"{nosaukums}.tif",
            mime="image/tiff",
            icon="💾",
        )

@st.dialog("Vai Jūs tiešām vēlaties dzēst karti?")
def izdzest_karti(uzdevuma_id):
    if st.button("Dzēst karti", icon="🗑️"):
        izdzest_uzdevumu_pec_id(uzdevuma_id)
        st.session_state.odm_uzdevumi=  None
        st.rerun()

st.title("Ortofoto kartes")
if st.session_state.tif_fails or st.session_state.odm_uzdevums:
    if not st.session_state.ortofoto_sensora_dati:
        dienas_diapzona = [st.session_state.ortofoto_sensora_datums, st.session_state.ortofoto_sensora_datums + datetime.timedelta(days=1)]
        st.session_state.ortofoto_sensora_dati = dabut_visus_sensora_ierakstus(dienas_diapzona)

        if st.session_state.ortofoto_sensora_dati:
            ieladet_sensora_datus()

    kartes_cilne, sensora_datu_cilne = st.tabs(["Karte", "Sensora dati"])

    with kartes_cilne:
        datumu_kolonna, laika_kolonna, tuksa_kolonna, atiestatit_kolona = st.columns([3, 3, 8, 1])

        with datumu_kolonna:
            izveletais_datums = st.date_input("Sensora datu datums:", format="DD.MM.YYYY", value=st.session_state.ortofoto_sensora_datums)

            if not izveletais_datums == st.session_state.ortofoto_sensora_datums:
                st.session_state.ortofoto_sensora_datums = izveletais_datums
                tif_datuma_izmaina()
                st.rerun()
        with laika_kolonna:
            izveletais_laiks = st.time_input("Sensora datu laiks:", value=st.session_state.ortofoto_sensora_laiks)

            if not izveletais_laiks == st.session_state.ortofoto_sensora_laiks:
                st.session_state.ortofoto_sensora_laiks = izveletais_laiks
                st.rerun()
        with atiestatit_kolona:
            st.button("❌", on_click=uzstadit_state, help="Aizvērt karti")

        kartes_konteineris = st.container()

        bez_koordinatas_ierices = [ierices_id for ierices_id, ierices_dati in st.session_state.sensora_ierices.items() if not ierices_dati["koordinatas"][0]]
        ar_koordinatas_ierices = [ierices_id for ierices_id, ierices_dati in st.session_state.sensora_ierices.items() if ierices_dati["koordinatas"][0]]

        koord_izveles_cilne, koord_redigesanas_cilne = st.tabs(["Koordinātas izvēle", "Koordinātas rediģēšana"])
        with koord_izveles_cilne:
            if bez_koordinatas_ierices:
                #st.info(f"Nepieciešams izvēlēties koordinātas {len(bez_koordinatas_ierices)} ierīcēm: {', '.join(bez_koordinatas_ierices)}.")
                izveleta_ierice = st.selectbox("Izvēlies ierīci, kurai uzstādīt koordinātas:", bez_koordinatas_ierices)

                if not st.session_state.spiediena_rezims:
                    st.button("Izvēlēties koordinātas", icon="🗺️", on_click=lambda: st.session_state.update(spiediena_rezims=True))
                else:
                    st.button("Apstiprināt koordinātas", icon="💾", on_click=apstiprinat_koordinatu, args=(izveleta_ierice, ))
            else:
                st.info("Visas sensoru ierīces koordinātas ir iestatītas. Lai rediģētu vai dzēstu koordinātas, dodaties uz 'Koordinātas rediģēšana' cilni.")
        with koord_redigesanas_cilne:
            if ar_koordinatas_ierices:
                darbiba = st.selectbox("Izvēlies rediģēšanas darbību:", ["Mainīt koordinātas", "Dzēst koordinatas"])
                darbibas_ierice = st.selectbox("Izvēlaties sensora ierīci:", ar_koordinatas_ierices)
            else:
                st.info("Nevienai sensora ierīcei nav uzstādītas koordinātas. Lai uzstādītu koordinātas, dotaties uz 'Koordinātas izvēle' cilni.")
        with kartes_konteineris:
            renderet_karti()

    with sensora_datu_cilne:
        if st.session_state.ortofoto_sensora_dati:
            st.subheader(f"Sensora dati datumā: {st.session_state.ortofoto_sensora_datums}")
            zimet_sensora_datus(st.session_state.ortofoto_sensora_dati)
        else:
            st.info(f"Sensora dati nav pieejami {st.session_state.ortofoto_sensora_datums.strftime('%d.%m.%Y')}. Lūdzu izvēlaties citu datumu!", icon="ℹ️")
else:
    datu_atjauninasanas_kolonna, tuksa_kolonna, tif_izveles_kolonna = st.columns([1.5, 3.5, 1.5])
    with datu_atjauninasanas_kolonna:
        st.button("Atjaunināt sarakstu", on_click=lambda: st.session_state.update(odm_uzdevumi=dabut_lietotaja_uzdevumus()), icon="🔄")
    with tif_izveles_kolonna:
        st.button("Atvērt GeoTIFF failu", icon="📂", on_click=izvēlēties_failu)

    if not st.session_state.odm_uzdevumi:
        st.session_state.odm_uzdevumi= dabut_lietotaja_uzdevumus()

    if st.session_state.odm_uzdevumi:
        for i, uzdevums in enumerate(st.session_state.odm_uzdevumi):
            with st.container(border=True):
                dt = datetime.datetime.strptime(uzdevums["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
                uzdevuma_id = uzdevums["id"]

                col1, col2, col3, col4, col5 = st.columns([5, 1.9, 0.6, 0.6, 0.6])
                with col1:
                    st.text(f"{i+1} . {uzdevums['name']}")
                with col2:
                    st.text(f"{dt.strftime('%d.%m.%Y %H:%M')} ⚙️: {5-uzdevums['options'][0]['value']}")
                with col3:
                    st.button("🗺️", key="izvele_"+uzdevuma_id, disabled=not uzdevums["status"]==40, help="Atvērt ortofoto karti" if uzdevums["status"]==40 else "Karte tiek izveidota", on_click=izveleties_karti, args=(uzdevums,))
                with col4:
                    st.button("💾", key="lejup_"+uzdevuma_id, on_click=lejupladet_karti, args=(uzdevuma_id, uzdevums["name"]), help="Saglabāt GeoTIFF failu")
                with col5:
                    st.button("🗑️", key="dzest_"+uzdevuma_id, on_click=izdzest_karti, args=(uzdevuma_id,), help="Dzēst GeoTIFF karti")
    else:
        st.info('Sistēmā netika atrasta neviena karte. Lai izveidotu karti, dodaties uz "Kartes Izveide" lapu.')
