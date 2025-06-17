# Sensoru un bezpilota gaisa kuģa datu integrācija ģeogrāfiskajās informācijas sistēmās (ĢIS)

Šis repozitorijs satur bakalaura darba ietvaros izstrādātu atvērtā pirmkoda tīmekļa lietotnes prototipu. Sistēma apvieno bezpilota gaisa kuģa (drona) ortofoto attēlus un sensoru (temperatūra un mitrums) datus vienotā ģeogrāfiskās informācijas sistēmā (ĢIS), nodrošinot lauksaimniekiem intuitīvu veidu vizuālai datu analīzei.

![Tīmekļa Vietne](screenshots/TimeklaVietne.png 'Tīmekļa Vietne')

## 📌 Funkcionalitāte

- 🔐 Autentifikācija ar Google kontu (OAuth 2.0)
- 🛰️ Ortofoto izveide no dronu attēliem (WebODM API)
- 🎛️ Izveidoto ortofoto pārvaldes sistēma (GeoTIFF lejupielāde, ortofoto apskate un dzēšana)
- 🌿 VARI (Vegetation Atmospheric Resistance Index) kartes ģenerēšana
- 🗺️ Sensoru datu vizualizācija kartē (Folium)
- 📈 Sensoru datu filtrēšana un attēlošana interaktīvās diagrammās (Altair)
- 📍 Manuāla sensoru koordinātu uzstādīšana uz kartes
- 👤 Lietotāju segmentācija ar personalizētiem WebODM projektiem
- 🔐 Drošība: šifrētas sīkdatnes, SQL vaicājumu aizsardzība, konfidenciālu datu slēpšana

## 🛠️ Izmantotās tehnoloģijas

### Priekšpuse
- **Streamlit** – UI, navigācija, OAuth integrācija
- **Folium + streamlit-folium** – karšu skats, datu slāņi
- **Altair** – sensoru datu diagrammas
- **Pandas, NumPy** – datu apstrāde
- **Pillow, Rasterio, PyProj** – GeoTIFF failu pārveide

### Aizmugure
- **PostgreSQL** – relāciju datubāze (lietotāji, koordinātas, datumi)
- **WebODM** – attēlu apstrāde, ortofoto/VARI izveide
- **Google OAuth 2.0** – autentifikācija
- **psycopg2** – SQL piekļuve un vaicājumi

## 📂 Projekta struktūra

```
📁 app/
├── pages/                # Tīmekļa lapas (Streamlit)
├── db/                   # PostgreSQL savienojums un funkcijas
├── api/                  # WebODM un sensora API pieprasījumu funkcijas
├── utils/                # Palīgfunkcijas (ĢIS, datu diagrammas, stils)
├── .streamlit            # Privātie dati (secrets.toml)
├── requirements.txt      # Pakotņu atkarības
├── script.py             # Galvenais Streamlit fails
├── secrets.toml.example  # secrets.toml piemēra/demonstrācijas fails
```

## 🔐 Prasības

- Python 3.10+
- PostgreSQL datu bāze ar struktūru:
  
![PostgreSQL ER](screenshots/PostgreSQLERDiagramma.png 'PostgreSQL ER')
- WebODM Docker instance (seko: https://github.com/OpenDroneMap/WebODM?tab=readme-ov-file#manual-installation-docker)
- Google OAuth 2.0 klienta ID un noslēpums
- Sensora datu API serveris, kas atbilst bakalaura darbā aprakstītai struktūrai

## 🔧 Uzstādīšana (lokāli)

1. Klonē repozitoriju:

```bash
git https://github.com/jacob-konosx/BakalauraDarbs.git
cd BakalauraDarbs
```

2. Izveido un aktivizē virtuālo vidi:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Instalē atkarības:

```bash
pip install -r requirements.txt
```

4. Seko *secrets.toml.example* piemēram un uzstādi slepenos mainīgos *./streamlit/secrets.toml* failā

5. Palaid Streamlit lietotni:

```bash
streamlit run script.py
```
