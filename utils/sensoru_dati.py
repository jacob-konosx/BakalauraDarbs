import datetime
import streamlit as st
import pandas as pd
import altair as alt
from api.pieprasijumi import dabut_sensora_datus
from db.db import db_dabut_sensoru_koordinatas_pec_uzdevuma_id, db_izveidot_sensoru_koordinatas

opcijas = {
    "air temperature": "Gaisa Temperatūra (°C)",
    "air humidity": "Gaisa Mitrums (%)",
    "soil temperature 1": "Augsnes Temperatūra 1 (°C)",
    "soil temperature 2": "Augsnes Temperatūra 2 (°C)",
    "soil moisture 1": "Augsnes Mitrums 1 (%)",
    "soil moisture 2": "Augsnes Mitrums 2 (%)",
}

@st.cache_data
def izveidot_sensora_ierices(visi_ieraksti):
    sensora_ierices = {}

    pirma_ieraksta_datetime = datetime.datetime.strptime(visi_ieraksti[0]["s_date"], "%Y-%m-%dT%H:%M:%SZ")
    ortofoto_sensora_laiks = datetime.time(hour=pirma_ieraksta_datetime.hour, minute=pirma_ieraksta_datetime.minute)

    for datu_ieraksts in visi_ieraksti:
        if datu_ieraksts["device id"] not in sensora_ierices:
            sensora_ierices[datu_ieraksts["device id"]] = {
                "koordinatas": [None, None],
                "dati": []
            }
        sensora_ierices[datu_ieraksts["device id"]]["dati"].append(datu_ieraksts)

    return sensora_ierices, ortofoto_sensora_laiks

def ieladet_sensora_datus():
    st.session_state.sensora_ierices, st.session_state.ortofoto_sensora_laiks = izveidot_sensora_ierices(st.session_state.ortofoto_sensora_dati)

    if st.session_state.odm_uzdevums:
        db_sensoru_koordinatas = db_dabut_sensoru_koordinatas_pec_uzdevuma_id(st.session_state.odm_uzdevums["id"])

        if db_sensoru_koordinatas:
            for koordinata in db_sensoru_koordinatas:
                st.session_state.sensora_ierices[koordinata["sensora_id"]]["koordinatas"] = [koordinata["platums"], koordinata["garums"]]
        else:
            for sensora_id in st.session_state.sensora_ierices:
                db_izveidot_sensoru_koordinatas(st.session_state.odm_uzdevums["id"], sensora_id, [None, None])

@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_visus_sensora_ierakstus(datumu_diapzona):
    visi_ieraksti = []

    try:
        str_diapzona = [datumu_diapzona[i].strftime("%b").upper() + str(datumu_diapzona[i].day).zfill(2) + str(datumu_diapzona[i].year) for i in range(2)]
        sensora_dati = dabut_sensora_datus(st.secrets.sensoru_datu_url.format(str_diapzona[0], str_diapzona[1]))

        visi_ieraksti += sensora_dati["items"]
        while sensora_dati["hasMore"]:
            jaunais_datu_url = [link for link in sensora_dati["links"] if "next" in link["rel"]]

            sensora_dati = dabut_sensora_datus(jaunais_datu_url[0]["href"])

            if sensora_dati:
                visi_ieraksti += sensora_dati["items"]

        if visi_ieraksti:
            return visi_ieraksti
        else:
            st.warning("Sensora dati nav pieejami datuma diapzonā!", icon="⚠️")
    except:
        st.toast("Neizdevās pieprasīt sensora datus.", icon="🚨")

@st.cache_data
def iestatit_df(sensora_dati):
    df = pd.DataFrame(sensora_dati)

    df["Datums"] = pd.to_datetime(df["s_date"], utc=True).dt.tz_localize(None)
    df["Sensora ID"] = df["device id"]

    df[list(opcijas.values())] = df[list(opcijas.keys())].astype(float)

    return df

def zimet_sensora_datus(sensora_dati):
    df = iestatit_df(sensora_dati)
    izveleta_opcija = st.selectbox("Datu kategorijas: ", list(opcijas.values()))

    diagramma = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Datums:T", title="Laiks", axis=alt.Axis(format="%H:%M")),
            y=alt.Y(f"{izveleta_opcija}:Q", title=izveleta_opcija),
            color=alt.Color("Sensora ID:N", title="Sensoru ID"),
            tooltip=[
                alt.Tooltip('Datums:T', title='Laiks', format='%H:%M:%S'),
                "Datums:T",
                f"{izveleta_opcija}:Q",
                "Sensora ID:N"
            ]
        )
        .interactive()
    )

    st.altair_chart(diagramma)
