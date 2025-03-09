import rasterio, folium, base64
import numpy as np
import streamlit as st
from streamlit_folium import folium_static
from folium.raster_layers import ImageOverlay
from pyproj import Transformer
from PIL import Image

from io import BytesIO

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
    img.save(buffered, format="PNG")
    # Konvertēt bonaro attēlu formātu uz virknes
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Izveidot datu URL
    data_url = f"data:image/png;base64,{img_str}"


    # Izveidot Folium karti contrtu uz TIF centru
    m = folium.Map(location=[center_lat, center_lon], zoom_start=20)

    folium.TileLayer(
        tiles="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}@2x?access_token=" + st.secrets.MAPBOX_ACCESS_TOKEN,
        attr="Mapbox",
        name="Satellite",
        overlay=False,
        control=True,
        max_zoom=22
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

    folium_static(m)
