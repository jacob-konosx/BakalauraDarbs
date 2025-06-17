import datetime, json
from streamlit_folium import st_folium, folium_static
import streamlit as st
from utils.sensoru_dati import zimet_sensora_datus, dabut_visus_sensora_ierakstus, ieladet_sensora_datus
from api.pieprasijumi import dabut_lietotaja_uzdevumus, lejupladet_tif_pec_id, izdzest_uzdevumu_pec_id, dabut_uzdevuma_info_pec_id
from db.db import db_dabut_odm_uzdevumu_pec_id, db_atjauninat_odm_uzdevuma_datumu_pec_id, db_atjauninat_sensora_koordinatas_pec_id, db_dzest_sensora_koordinatas_pec_uzdevuma_id, db_dzest_odm_uzdevumu_pec_id
from utils.karte import izveidot_karti

KARTES_AUGSTUMS = 700

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

def apstiprinat_koordinatu(sensora_id):
    if st.session_state.odm_uzdevums:
        db_atjauninat_sensora_koordinatas_pec_id(st.session_state.odm_uzdevums["id"], sensora_id, st.session_state.izveleta_koordinate)

    st.session_state.sensora_ierices[sensora_id]["koordinatas"] = st.session_state.izveleta_koordinate
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None

def tif_datuma_izmaina():
    st.session_state.ortofoto_sensora_laiks = datetime.time(0, 0)
    st.session_state.spiediena_rezims = False
    st.session_state.izveleta_koordinate = None
    st.session_state.sensora_ierices = {}
    st.session_state.ortofoto_sensora_dati = None

    if st.session_state.odm_uzdevums:
        db_atjauninat_odm_uzdevuma_datumu_pec_id(st.session_state.odm_uzdevums["id"], st.session_state.ortofoto_sensora_datums)
        db_dzest_sensora_koordinatas_pec_uzdevuma_id(st.session_state.odm_uzdevums["id"])

if "odm_uzdevumi" not in st.session_state:
    uzstadit_state()

def izveleties_karti(uzdevuma_id):
    odm_uzdevums = dabut_uzdevuma_info_pec_id(uzdevuma_id)
    db_odm_uzdevums = db_dabut_odm_uzdevumu_pec_id(uzdevuma_id)

    if db_odm_uzdevums:
        st.session_state.ortofoto_sensora_datums = db_odm_uzdevums["datums"]
        st.session_state.odm_uzdevums = odm_uzdevums

def dzest_koordinatu(sensora_id):
    st.session_state.sensora_ierices[sensora_id]["koordinatas"] = [None, None]

    if st.session_state.odm_uzdevums:
        db_atjauninat_sensora_koordinatas_pec_id(st.session_state.odm_uzdevums["id"], sensora_id, [None, None])

def uzstadit_uzdevumu_sarakstu():
    odm_uzdevumi= dabut_lietotaja_uzdevumus()

    if odm_uzdevumi:
        odm_uzdevumi.sort(key=lambda uzdevums: uzdevums["created_at"], reverse=True)
        st.session_state.odm_uzdevumi = odm_uzdevumi

@st.dialog("Izvēlaties GeoTIFF kartes failu")
def izvēlēties_failu():
    st.warning("Kartes operācijas ar GeoTIFF failu būs ievērojami lēnākas nekā caur sistēmas kartes izveides procesu! Kā arī sensoru koordinātas saglabāšana un VARI karte nebūs pieejama!", icon="⚠️")
    st.page_link("pages/ortofoto_izveide.py", label="Doties uz kartes izveidi", icon="🪡")

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
        db_dzest_odm_uzdevumu_pec_id(uzdevuma_id)
        izdzest_uzdevumu_pec_id(uzdevuma_id)
        st.session_state.odm_uzdevumi=  None
        st.rerun()

if st.session_state.tif_fails or st.session_state.odm_uzdevums:
    if st.session_state.odm_uzdevums:
        st.title(f"Karte - {st.session_state.odm_uzdevums['name']}")
    else:
        st.title("GeoTIFF karte")

    if not st.session_state.ortofoto_sensora_dati:
        dienas_diapzona = [st.session_state.ortofoto_sensora_datums, st.session_state.ortofoto_sensora_datums + datetime.timedelta(days=1)]
        st.session_state.ortofoto_sensora_dati = dabut_visus_sensora_ierakstus(dienas_diapzona)

        if st.session_state.ortofoto_sensora_dati:
            ieladet_sensora_datus()

    kartes_cilne, sensoru_datu_cilne = st.tabs(["Karte", "Sensoru dati"])

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

        m = izveidot_karti(
            st.session_state.izveleta_koordinate,
            st.session_state.sensora_ierices,
            st.session_state.ortofoto_sensora_laiks,
            json.loads(st.session_state.sikdatne["galvene"]),
            st.session_state.odm_uzdevums,
            st.session_state.tif_fails
        )

        kartes_dati = st_folium(
            m,
            width=None,
            height=KARTES_AUGSTUMS,
        )

        if st.session_state.spiediena_rezims:
            if kartes_dati.get("last_clicked") :
                lat = kartes_dati["last_clicked"]["lat"]
                lon = kartes_dati["last_clicked"]["lng"]
                st.session_state.izveleta_koordinate = [lat, lon]
                st.rerun()

        bez_koordinatas_sensoru_id = [ierices_id for ierices_id, ierices_dati in st.session_state.sensora_ierices.items() if not ierices_dati["koordinatas"][0]]
        ar_koordinatas_sensoru_id = [ierices_id for ierices_id, ierices_dati in st.session_state.sensora_ierices.items() if ierices_dati["koordinatas"][0]]

        darbibas = {}
        if bez_koordinatas_sensoru_id:
            darbibas["📌 Uzstādīt sensora koordinātu"] = 0
        if ar_koordinatas_sensoru_id:
            darbibas["✍🏼 Mainīt koordinātas"] = 1
            darbibas["🗑️ Dzēst koordinatas"] = 2

        if darbibas:
            darbiba = st.selectbox("Izvēlies sensoru koordinātas darbību:", darbibas)

            if not darbibas[darbiba] == 2:
                    if darbibas[darbiba] == 0:
                        sensora_id = st.selectbox("Izvēlies sensoru, kuram uzstādīt koordinātas:", bez_koordinatas_sensoru_id)
                    else:
                        sensora_id = st.selectbox("Izvēlaties sensoru, kuram mainīt koordinātu:", ar_koordinatas_sensoru_id)

                    if not st.session_state.spiediena_rezims:
                        st.button("Izvēlēties koordinātu", icon="🗺️", on_click=lambda:st.session_state.update(spiediena_rezims=True))
                    else:
                        st.button("Apstiprināt koordinātu", icon="💾", on_click=apstiprinat_koordinatu, args=(sensora_id, ), disabled=st.session_state.izveleta_koordinate==None)
                        st.button("Atcelt koordinatu izvēli", icon="❌", on_click=lambda: st.session_state.update({"spiediena_rezims":False, "izveleta_koordinate":None}))
            else:
                dzesama_sensora_id = st.selectbox("Izvēlaties sensoru, kuram dzēst koordinātu:", ar_koordinatas_sensoru_id)
                st.button("Dzēst koordinātu", icon="🗑️", on_click=dzest_koordinatu, args=(dzesama_sensora_id, ))

    with sensoru_datu_cilne:
        if st.session_state.ortofoto_sensora_dati:
            st.subheader(f"Sensora dati datumā: {st.session_state.ortofoto_sensora_datums}")
            zimet_sensora_datus(st.session_state.ortofoto_sensora_dati)
        else:
            st.info(f"Sensora dati nav pieejami {st.session_state.ortofoto_sensora_datums.strftime('%d.%m.%Y')}. Lūdzu izvēlaties citu datumu!", icon="ℹ️")
else:
    st.title("Manas ortofoto kartes")
    datu_atjauninasanas_kolonna, tuksa_kolonna, tif_izveles_kolonna = st.columns([1.5, 5, 1.5])
    with datu_atjauninasanas_kolonna:
        st.button("Atjaunināt", on_click=uzstadit_uzdevumu_sarakstu, icon="🔄")
    with tif_izveles_kolonna:
        st.button("Atvērt GeoTIFF", icon="📂", on_click=izvēlēties_failu)

    if not st.session_state.odm_uzdevumi:
        uzstadit_uzdevumu_sarakstu()

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
                    st.button("🗺️", key="izvele_"+uzdevuma_id,
                        disabled=not uzdevums["status"]==40,
                        help="Atvērt ortofoto karti" if uzdevums["status"]==40 else "Karte tiek izveidota",
                        on_click=izveleties_karti,
                        args=(uzdevuma_id,)
                    )
                with col4:
                    st.button("💾", key="lejup_"+uzdevuma_id,
                        disabled=not uzdevums["status"]==40,
                        on_click=lejupladet_karti,
                        args=(uzdevuma_id, uzdevums["name"]),
                        help="Saglabāt GeoTIFF failu"
                    )
                with col5:
                    st.button("🗑️", key="dzest_"+uzdevuma_id, on_click=izdzest_karti, args=(uzdevuma_id,), help="Dzēst GeoTIFF karti")
    else:
        st.info('Sistēmā netika atrasta neviena karte. Lai izveidotu karti, dodaties uz "Kartes Izveide" lapu.')
