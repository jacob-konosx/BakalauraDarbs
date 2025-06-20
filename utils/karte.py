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
from utils.sensoru_dati import opcijas

ZOOM_START = 21
MIN_ZOOM = 19
MAX_ZOOM = 35

@st.cache_data
def dabut_krasu(vertiba, tips):
    if "temp" in tips:
        min_vertiba, max_vertiba = (0, 40)
        krasa = linear.YlOrRd_09.scale(min_vertiba, max_vertiba)
    elif "humidity" in tips:
        min_vertiba, max_vertiba = (0, 100)
        krasa = linear.Blues_09.scale(min_vertiba, max_vertiba)
    else:
        min_vertiba, max_vertiba= (0, 50)
        krasa = linear.Greens_09.scale(min_vertiba, max_vertiba)

    return krasa(float(vertiba))

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

    # Uztaisīt transformeru no ODM CRS uz EPSG:4326, kas ir nepieciešama priekš folium
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    # Pārvērtiet robežas no projektētās CRS uz EPSG:4326
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
def izveidot_karti(izveleta_koordinate, visas_sensora_ierices, ortofoto_sensora_laiks, galvene, odm_uzdevums=None, tif_fails=None):
    if odm_uzdevums:
        centra_lat, centra_lon = izrekinat_ortofoto_centru(odm_uzdevums["extent"])
    else:
        centra_lat, centra_lon, data_url, folium_robeza = ieladet_tif_datus(tif_fails)

    # Izveidot Folium karti contrtu uz ortofoto centru
    m = folium.Map(location=[centra_lat, centra_lon], tiles=None, zoom_start=ZOOM_START, max_zoom=MAX_ZOOM, min_zoom=MIN_ZOOM)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr="Esri, TomTom, Garmin, FAO, NOAA, USGS",
        name="Satelīta flīzes",
        overlay=False,
        zoom_start=ZOOM_START,
        max_zoom=MAX_ZOOM,
        min_zoom=MIN_ZOOM,
        max_native_zoom= 20,
        show=True,
        z_index=1,
    ).add_to(m)

    odm_ortofoto = None
    if odm_uzdevums:
        ortofoto_flizes_url = f"{st.secrets.odm_url}/projects/{st.session_state.sikdatne['odm_projekta_id']}/tasks/{odm_uzdevums['id']}/orthophoto/tiles/{{z}}/{{x}}/{{y}}?jwt={galvene['Authorization'].replace('JWT ', '')}"

        odm_ortofoto = folium.TileLayer(
            tiles=ortofoto_flizes_url,
            attr='WebODM ortofoto',
            name='Ortofoto karte',
            overlay=True,
            z_index=10,
            zoom_start=ZOOM_START,
            max_zoom=MAX_ZOOM,
            min_zoom=MIN_ZOOM
        ).add_to(m)

        vari = folium.TileLayer(
            tiles=ortofoto_flizes_url+"&formula=VARI&bands=auto&color_map=rdylgn&rescale=-0.19014084507042253,0.19827586206896552",
            attr='WebODM VARI',
            name='VARI',
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

    slani = {}
    if visas_sensora_ierices:
        sensora_ierices_ar_koord =  {a: v for a, v in visas_sensora_ierices.items() if v.get("koordinatas")[0] is not None}

        for sensora_ierices_id, sensora_datu_ieraksts in sensora_ierices_ar_koord.items():
            sensoru_datu_ieraksts = None
            for ieraksts in sensora_datu_ieraksts["dati"]:
                s_date_datetime = datetime.strptime(ieraksts["s_date"], "%Y-%m-%dT%H:%M:%SZ")
                if s_date_datetime.minute == ortofoto_sensora_laiks.minute and s_date_datetime.hour == ortofoto_sensora_laiks.hour:
                    sensoru_datu_ieraksts = {a: v for a, v in ieraksts.items() if a not in ["device id", "s_date"] and not v == None}
                    break

            if sensoru_datu_ieraksts:
                for merijuma_nosaukums in sensoru_datu_ieraksts:
                    datu_nosaukums = opcijas[merijuma_nosaukums]
                    if not slani.get(merijuma_nosaukums):
                        slani[merijuma_nosaukums] = folium.FeatureGroup(
                            name=datu_nosaukums,
                            show=True if "air temperature" in merijuma_nosaukums else False,
                            overlay=True,
                            zindex=10
                        ).add_to(m)

                    merijuma_vertiba = sensoru_datu_ieraksts[merijuma_nosaukums]
                    robezas_krasa = "white" if "air" in merijuma_nosaukums else "brown"
                    vertibas_virkne = f"{merijuma_vertiba}  {'°C' if 'temp' in merijuma_nosaukums else '%'}"

                    folium.Circle(
                        location=sensora_datu_ieraksts["koordinatas"],
                        radius=4 if "soil" in merijuma_nosaukums else 5,
                        color=robezas_krasa,
                        fill=True,
                        fill_color=dabut_krasu(merijuma_vertiba, merijuma_nosaukums),
                        fill_opacity=0.2,
                        popup=f"{datu_nosaukums}: {merijuma_vertiba}",
                        weight=1,
                        tooltip=vertibas_virkne,
                    ).add_to(slani.get(merijuma_nosaukums))

            folium.Circle(
                location=sensora_datu_ieraksts["koordinatas"],
                radius=0.2,
                fill_opacity=0,
                popup=f"Ierīce: {sensora_ierices_id}, Koordinātas: {sensora_datu_ieraksts['koordinatas']}",
                fill=True,
                zindex=20
            ).add_to(m)

        if sensora_ierices_ar_koord:
            folium.plugins.GroupedLayerControl(
                groups={
                    'Sensoru datu slāņi': list(slani.values())
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

    if odm_uzdevums:
        folium.plugins.GroupedLayerControl(
            groups={
                'Ortofoto slāņi': [odm_ortofoto, vari]
            },
            exclusive_groups=True,
            collapsed=False,
        ).add_to(m)

    return m
