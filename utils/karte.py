import rasterio, folium, base64
import numpy as np
import streamlit as st
import branca.colormap as cm
from folium.raster_layers import ImageOverlay
from pyproj import Transformer
from PIL import Image
from io import BytesIO
from datetime import datetime


@st.cache_data
def temp_krasa(temp, tips):
    min_temp, max_temp = (0, 40) if "temp" in tips else (0, 100)
    krasa = cm.linear.YlOrRd_09.scale(min_temp, max_temp)

    return krasa(float(temp))

@st.cache_data(show_spinner="Tiek ielādēti TIF dati")
def ieladet_datus(tif):
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

    # Aprēķināt attēla centru
    centra_lon = (left_lon + right_lon) / 2
    centra_lat = (bottom_lat + top_lat) / 2

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
def izveidot_karti(ir_satelita_flizes, izveleta_koordinate, ierices, tif_laiks):
    centra_lat, centra_lon, data_url, folium_robeza = ieladet_datus(st.session_state.tif_fails)

    # Izveidot Folium karti contrtu uz TIF centru
    m = folium.Map(location=[centra_lat, centra_lon], zoom_start=21, max_zoom=25, min_zoom=19, max_bounds=True)

    if ir_satelita_flizes:
        folium.TileLayer(
            tiles="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}@2x?access_token=" + st.secrets.mapbox_access_token,
            attr="Mapbox",
            name="Satellite",
            overlay=False,
            control=True,
            max_zoom=25
        ).add_to(m)

    if len(ierices) > 0:
        slani = {}
        for slanis in st.session_state.datu_slani:
            slani[slanis] = folium.FeatureGroup(name=slanis, show=True if "air temperature" in slanis else False).add_to(m)

        for ierices_id, ierices_dati in ierices.items():
            if ierices_dati["koordinatas"]:
                datu_ieraksts = None

                for ieraksts in ierices_dati["dati"]:
                    s_date_datetime = datetime.strptime(ieraksts["s_date"], "%Y-%m-%dT%H:%M:%SZ")
                    if s_date_datetime.minute == tif_laiks.minute and s_date_datetime.hour == tif_laiks.hour:
                        datu_ieraksts = ieraksts
                        break

                if datu_ieraksts:
                    for datu_tips in datu_ieraksts:
                        dati = datu_ieraksts[datu_tips]

                        if datu_tips in st.session_state.datu_slani and dati:
                            folium.Circle(
                                location=ierices_dati["koordinatas"],
                                radius=4 if "soil" in datu_tips else 5,
                                color=temp_krasa(dati, datu_tips),
                                fill=True,
                                fill_color=temp_krasa(dati, datu_tips),
                                fill_opacity=0.2,
                                popup=f"{datu_tips}: {dati}",
                                weight=1
                            ).add_to(slani.get(datu_tips))

                folium.Circle(
                    location=ierices_dati["koordinatas"],
                    radius=0.2,
                    fill_opacity=0,
                    popup=f"Ierīce: {ierices_id}, Koordinātas: {ierices_dati['koordinatas']}",
                    fill=True,
                    zindex=2
                ).add_to(m)

    if izveleta_koordinate:
        folium.Circle(
            location=izveleta_koordinate,
            radius=0.2,
            fill_opacity = 1,
            color="#bd0026ff"
        ).add_to(m)

    # Pievienot GeoTIFF pārklājumu virs karti
    ImageOverlay(
        name="Ortofoto",
        image=data_url,
        bounds=folium_robeza,
        opacity=1,
        interactive=True,
        cross_origin=False,
        zindex=1,
        max_zoom=30
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m
