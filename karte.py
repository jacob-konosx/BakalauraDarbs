import rasterio, folium, base64
import numpy as np
import streamlit as st
import branca.colormap as cm
from streamlit_folium import st_folium
from folium.raster_layers import ImageOverlay
from pyproj import Transformer
from PIL import Image
from io import BytesIO

def temp_krasa(temp, min_temp=0, max_temp=40):
    colormap = cm.linear.YlOrRd_09.scale(min_temp, max_temp)
    return colormap(temp)

def zimet_karti(tif):
    # Atver GeoTIF failu ar rosterio
    with rasterio.open(tif) as src:
        # Dabū TIF robežas
        robeza = src.bounds
        crs = src.crs  # Dabūt CRS (Coordinate Reference System)

        attels = src.read([1, 2, 3])  # Izlasit tikai RGB vērtības

    # Uztaisīt transformeru no WebODM CRS uz WGS84, kas ir nepieciešama priekš folium
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    # Pārvērtiet robežas no projektētās CRS uz WGS84
    left_lon, bottom_lat = transformer.transform(robeza.left, robeza.bottom)
    right_lon, top_lat = transformer.transform(robeza.right, robeza.top)

    # Aprēķināt attēla centru
    center_lon = (left_lon + right_lon) / 2
    center_lat = (bottom_lat + top_lat) / 2

    # Izveidot folium robežas
    folium_robeza = [[bottom_lat, left_lon], [top_lat, right_lon]]

    # Pārvērst attēlu masīvu uz numpy
    attels = np.transpose(attels, (1, 2, 0))  # Izmainīt attēla formu (bands, height, width) uz (height, width, bands)

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


    # Izveidot Folium karti contrtu uz TIF centru
    m = folium.Map(location=[center_lat, center_lon], zoom_start=20)

    folium.TileLayer(
        tiles="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}@2x?access_token=" + st.secrets.mapbox_access_token,
        attr="Mapbox",
        name="Satellite",
        overlay=False,
        control=True,
        max_zoom=30
    ).add_to(m)


    for punkts in st.session_state.temp_punkti:
        folium.Circle(
            location=[punkts["lat"], punkts["lon"]],
            radius=5,
            color=temp_krasa(punkts["temp"]),
            fill=True,
            fill_color=temp_krasa(punkts["temp"]),
            fill_opacity=0.2,
            popup=f"Teperatūra: {punkts['temp']}°C",
            weight=1
        ).add_to(m)

    # Pievienot GeoTIFF pārklājumu virs karti
    ImageOverlay(
        name="Orthophoto",
        image=data_url,
        bounds=folium_robeza,
        opacity=1,
        interactive=True,
        cross_origin=False,
        zindex=1,
    ).add_to(m)

    # Pievienot slāņu kontroli
    folium.LayerControl().add_to(m)

    kartes_dati = st_folium(m, width=1000)

    last_clicked = None
    if kartes_dati and kartes_dati.get("last_clicked"):
        lat = kartes_dati["last_clicked"]["lat"]
        lon = kartes_dati["last_clicked"]["lng"]
        last_clicked = (lat, lon)

    if last_clicked:
        temp = st.number_input(f"Temperatūra (°C) punktā {last_clicked}", min_value=-50, max_value=50, step=1, value=0)

        if st.button("Pievienot temperatūas punktu"):
            st.session_state.temp_punkti.append({
                "lat": last_clicked[0],
                "lon": last_clicked[1],
                "temp": temp
            })

            st.rerun()
