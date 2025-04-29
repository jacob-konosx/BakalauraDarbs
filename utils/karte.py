import folium.plugins
import rasterio, folium, base64
import numpy as np
import streamlit as st
from branca.colormap import linear
from folium.raster_layers import ImageOverlay
from pyproj import Transformer
from PIL import Image
from io import BytesIO
from datetime import datetime

ZOOM_START = 21
MIN_ZOOM = 19
MAX_ZOOM = 35
STAMEN_FLIZES_URL = "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png"

@st.cache_data
def temp_krasa(temp, tips):

    if "temp" in tips:
        min_temp, max_temp = (0, 40)
        krasa = linear.YlOrRd_09.scale(min_temp, max_temp)
    else:
        min_temp, max_temp = (0, 100)
        krasa = linear.Blues_09.scale(min_temp, max_temp)

    return krasa(float(temp))

@st.cache_data
def izrekinat_ortofoto_centru(robeza):
    min_lon, min_lat, max_lon, max_lat = robeza

    # Aprēķināt attēla centru
    centra_lon = (min_lon + max_lon) / 2
    centra_lat = (min_lat + max_lat) / 2

    return centra_lat, centra_lon

@st.cache_data(show_spinner="Tiek ielādēti TIF dati")
def ieladet_tif_datus(tif):
    # Atver GeoTIF failu ar rosterio
    with rasterio.open(tif) as src:
        # Dabū TIF robežas
        robeza = src.bounds
        crs = src.crs  # Dabūt CRS (Coordinate Reference System)

        attels = src.read([1, 2, 3])  # Izlasit tikai RGB vērtības

    # Uztaisīt transformeru no ODM CRS uz WGS84, kas ir nepieciešama priekš folium
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    # Pārvērtiet robežas no projektētās CRS uz WGS84
    left_lon, bottom_lat = transformer.transform(robeza.left, robeza.bottom)
    right_lon, top_lat = transformer.transform(robeza.right, robeza.top)

    centra_lat, centra_lon = izrekinat_ortofoto_centru([left_lon, bottom_lat, right_lon, top_lat])

    # Izveidot folium robežas
    folium_robeza = [[bottom_lat, left_lon], [top_lat, right_lon]]

    # Pārvērst attēlu masīvu uz numpy
    attels = np.moveaxis(attels, 0, -1)  # Izmainīt attēla formu (bands, height, width) uz (height, width, bands)

    #Izveidot alfa kanālu, kur melns (0,0,0) ir TIF vietas, kur nav dati
    alpha_channel = np.where((attels == [0, 0, 0]).all(axis=-1), 0, 255).astype(np.uint8)

    # Pielikt alfa kanālu uz attēla
    image_rgba = np.dstack((attels, alpha_channel))


    img = Image.fromarray(image_rgba, "RGBA")

    buffered = BytesIO()
    img.save(buffered, format="PNG", optimized=True)
    # Konvertēt bonaro attēlu formātu uz virknes
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Izveidot datu URL
    data_url = f"data:image/png;base64,{img_str}"

    return centra_lat, centra_lon, data_url, folium_robeza

@st.cache_data(show_spinner="Tiek ģenerēta karte")
def izveidot_karti(izveleta_koordinate, sensora_ierices, ortofoto_sensora_laiks, odm_uzdevums=None, tif_fails=None):
    if odm_uzdevums:
        centra_lat, centra_lon = izrekinat_ortofoto_centru(odm_uzdevums["extent"])
    else:
        centra_lat, centra_lon, data_url, folium_robeza = ieladet_tif_datus(tif_fails)

    # Izveidot Folium karti contrtu uz TIF centru
    m = folium.Map(location=[centra_lat, centra_lon], tiles=None, zoom_start=ZOOM_START, max_zoom=MAX_ZOOM, min_zoom=MIN_ZOOM)

    if odm_uzdevums:
        ortofoto_flizes_url = f"{st.secrets.odm_url}/projects/{st.session_state.odm_projekta_id}/tasks/{odm_uzdevums['id']}/orthophoto/tiles/{{z}}/{{x}}/{{y}}.png?jwt={st.session_state.galvene['Authorization'].replace('JWT ', '')}"

        folium.TileLayer(
            tiles=ortofoto_flizes_url,
            attr='WebODM',
            name='Ortofoto flīzes',
            overlay=True,
            z_index=10,
            zoom_start=ZOOM_START,
            max_zoom=MAX_ZOOM,
            min_zoom=MIN_ZOOM
        ).add_to(m)
    elif tif_fails:
        # Pievienot GeoTIFF pārklājumu virs karti
        ImageOverlay(
            name="Ortofoto fails",
            image=data_url,
            bounds=folium_robeza,
            opacity=1,
            z_index=10,
            interactive=True,
            cross_origin=False,
            zoom_start=ZOOM_START,
            max_zoom=MAX_ZOOM,
            min_zoom=MIN_ZOOM
        ).add_to(m)

    satelita_flizes = folium.TileLayer(
        tiles="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}@2x?access_token=" + st.secrets.mapbox_access_token,
        attr="Mapbox",
        name="Satelīta flīzes",
        overlay=False,
        zoom_start=ZOOM_START,
        max_zoom=MAX_ZOOM,
        min_zoom=MIN_ZOOM
    )
    stamen_flizes = folium.TileLayer(
        tiles=STAMEN_FLIZES_URL,
        attr="Stamen",
        name="Stamen flīzes",
        overlay=False,
        zoom_start=ZOOM_START,
        max_zoom=MAX_ZOOM,
        min_zoom=MIN_ZOOM
        )

    satelita_flizes.add_to(m)
    stamen_flizes.add_to(m)
    folium.plugins.GroupedLayerControl(
        groups={
            'Kartes flīzes': [stamen_flizes, satelita_flizes],
        },
        exclusive_groups=True,
        collapsed=False,
    ).add_to(m)

    slani = {}
    if len(sensora_ierices) > 0:
        for slanis in st.session_state.datu_slani:
            slani[slanis] = folium.FeatureGroup(name=slanis, show=True if "air temperature" in slanis else False, overlay=True).add_to(m)

        for sensora_ierices_id, sensora_ierices_dati in sensora_ierices.items():
            if sensora_ierices_dati["koordinatas"]:
                datu_ieraksts = None

                for ieraksts in sensora_ierices_dati["dati"]:
                    s_date_datetime = datetime.strptime(ieraksts["s_date"], "%Y-%m-%dT%H:%M:%SZ")
                    if s_date_datetime.minute == ortofoto_sensora_laiks.minute and s_date_datetime.hour == ortofoto_sensora_laiks.hour:
                        datu_ieraksts = ieraksts
                        break

                if datu_ieraksts:
                    for datu_tips in datu_ieraksts:
                        dati = datu_ieraksts[datu_tips]

                        if datu_tips in st.session_state.datu_slani and dati:
                            vertiba = f"{dati}  {'°C' if 'temp' in datu_tips else '%'}"

                            folium.Circle(
                                location=sensora_ierices_dati["koordinatas"],
                                radius=4 if "soil" in datu_tips else 5,
                                color=temp_krasa(dati, datu_tips),
                                fill=True,
                                fill_color=temp_krasa(dati, datu_tips),
                                fill_opacity=0.2,
                                popup=f"{datu_tips}: {dati}",
                                weight=1,
                                tooltip=vertiba
                            ).add_to(slani.get(datu_tips))

                folium.Circle(
                    location=sensora_ierices_dati["koordinatas"],
                    radius=0.2,
                    fill_opacity=0,
                    popup=f"Ierīce: {sensora_ierices_id}, Koordinātas: {sensora_ierices_dati['koordinatas']}",
                    fill=True,
                    zindex=2
                ).add_to(m)
                
        folium.plugins.GroupedLayerControl(
            groups={
                'Info slāņi': list(slani.values())
            },
            exclusive_groups=False,
            collapsed=False,
        ).add_to(m)

    if izveleta_koordinate:
        folium.Circle(
            location=izveleta_koordinate,
            radius=0.2,
            fill_opacity = 1,
            color="#bd0026ff"
        ).add_to(m)

    return m
