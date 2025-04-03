import requests, datetime
import streamlit as st
import pandas as pd
import altair as alt


def dabut_str_diapzonu(diapzona):
    datu_str_diapzona = []
    for i in range(2):
        datu_str_diapzona.append(diapzona[i].strftime("%b").upper() + str(diapzona[i].day).zfill(2) + str(diapzona[i].year))

    return datu_str_diapzona

@st.cache_data
def ieladet_sensora_datus(tif_datums):
    sensoru_datu_saraksts = []
    str_diapzona = dabut_str_diapzonu([st.session_state.tif_datums, st.session_state.tif_datums + datetime.timedelta(days=1)])
    sensora_dati = dabut_sensora_datus(st.secrets.sensoru_datu_url.format(str_diapzona[0], str_diapzona[1]))

    if not len(sensora_dati["items"]) == 0:
        sensoru_datu_saraksts += sensora_dati["items"]
        st.session_state.datu_slani = [key for key in sensoru_datu_saraksts[0] if key not in ["device id", "s_date"]]

        pirma_ieraksta_datetime = datetime.datetime.strptime(sensora_dati["items"][0]["s_date"], "%Y-%m-%dT%H:%M:%SZ")
        st.session_state.tif_laiks = datetime.time(hour=pirma_ieraksta_datetime.hour, minute=pirma_ieraksta_datetime.minute)

        if sensora_dati["hasMore"]:
            sensoru_datu_saraksts += dabut_visus_items(sensora_dati)

        for datu_ieraksts in sensoru_datu_saraksts:
            if datu_ieraksts["device id"] not in st.session_state.ierices:
                st.session_state.ierices[datu_ieraksts["device id"]] = {
                        "koordinatas": None,
                        "dati": []
                    }

            st.session_state.ierices[datu_ieraksts["device id"]]["dati"].append(datu_ieraksts)
    return sensoru_datu_saraksts


@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_sensora_datus(sensora_datu_url):
    try:
        res = requests.get(sensora_datu_url)

        if res:
            json_res = res.json()
            return json_res
        else:
            return None
    except requests.exceptions.RequestException:
        return None

@st.cache_data(show_spinner="Tiek iegūti sensora dati")
def dabut_visus_items(sensora_dati):
    visi_items = []

    while sensora_dati["hasMore"]:
        jaunais_datu_url = [link for link in sensora_dati["links"] if "next" in link["rel"]]

        sensora_dati = dabut_sensora_datus(jaunais_datu_url[0]["href"])

        visi_items += sensora_dati["items"]

    return visi_items

def zimet_sensora_datus(sensora_dati):
    df = pd.DataFrame(sensora_dati)

    df["s_date"] = pd.to_datetime(df["s_date"], utc=True).dt.tz_localize(None)

    numeric_cols = ["air temperature", "air humidity", "soil temperature 1", "soil temperature 2", "soil moisture 1", "soil moisture 2"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    opcijas = {
        "Gaisa Temperatūra (°C)": "air temperature",
        "Gaisa Mitrums (%)": "air humidity",
        "Augsnes Temperatūra 1 (°C)": "soil temperature 1",
        "Augsnes Temperatūra 2 (°C)": "soil temperature 2",
        "Augsnes Mitrums 1 (%)": "soil moisture 1",
        "Augsnes Mitrums 2 (%)": "soil moisture 2",
    }

    izveleta_opcija = st.selectbox("Datu kategorijas: ", list(opcijas.keys()))

    opcija = opcijas[izveleta_opcija]

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("s_date:T", title="Laiks", axis=alt.Axis(format="%H:%M")),
            y=alt.Y(opcija + ":Q", title=izveleta_opcija),
            color=alt.Color("device id:N", title="Ierīces ID"),
            tooltip=["s_date:T", opcija + ":Q", "device id:N"]
        )
        .interactive()
    )

    st.write("")
    st.altair_chart(chart)
