import streamlit as st

MENESA_CSS = 'div[data-baseweb="popover"] > div > ul:has(> :nth-child(12)):not(:has(> :nth-child(13))) li'
MENESA_IZVELNES_CSS = 'div[aria-label="Calendar."] div:has(div[role="gridcell"][aria-label*="%s"]) div button:nth-child(2)'
DIENAS_SAISINAJUMA_CSS = 'div[aria-label="Calendar."] div[role="presentation"] div'

dienas = {
    1: "Sv",
    2: "P",
    3: "O",
    4: "T",
    5: "C",
    6: "Pk",
    7: "S"
}

menesi = {
    "Janvāris": "January",
    "Februāris": "February",
    "Marts": "March",
    "Aprīlis": "April",
    "Maijs": "May",
    "Jūnijs": "June",
    "Jūlijs": "July",
    "Augusts": "August",
    "Septembris": "September",
    "Oktobris": "October",
    "Novembris": "November",
    "Decembris": "December"
}

@st.cache_data
def dabut_stilu():
    MENESA_IZVELNES_TULKOJUMS = ""
    MENESU_TULKOJUMS = ""
    DIENAS_TULKOJUMS = ""
    for menesis in menesi.keys():
        MENESU_TULKOJUMS += f"""{MENESA_CSS}:nth-child({list(menesi).index(menesis)+1}):after {{
        visibility: visible;
        position: absolute;
        top: 10px;
        left: 10px;
        content: "{menesis}";
    }}"""

    for lv_menesis, en_menesis in menesi.items():
        MENESA_IZVELNES_TULKOJUMS += f"""{MENESA_IZVELNES_CSS % en_menesis} span:before {{
        visibility: visible;
        position: absolute;
        top: 17px;
        left: 5rem;
        content: "{lv_menesis}";
    }}"""

    for i, diena in dienas.items():
        DIENAS_TULKOJUMS += f"""{DIENAS_SAISINAJUMA_CSS}:nth-child({i}):after {{
        visibility: visible;
        position: absolute;
        top: 5px;
        left: 15px;
        content: "{diena}";
    }}"""

    return """
        <style>
            div[data-testid="stFileUploaderDropzoneInstructions"] div span, small {{
                display: none;
            }}

            div[data-testid="stFileUploaderDropzoneInstructions"] div::after {{
                content: "Izvēlēties .ZIP failu (400MB faila ierobežojums)";
            }}

            section[data-testid="stFileUploaderDropzone"]{{
                cursor: pointer;
            }}

            div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="stBaseButton-secondary"] {{
                display: none;
            }}

            .map-container {{
                width: 100%;
            }}

            .stText{{
                padding: 0.4rem 0px;
            }}

            div.st-key-CookieManager-sync_cookies{{
                display: none;
            }}

            div[data-testid="InputInstructions"] *{{
                display: none;
            }}

            div[data-testid="InputInstructions"]:after{{
                content: "Spiest Enter, lai apstiprinātu";
            }}

            {dienas_izvele} {{
                visibility: hidden;
            }}
            {dienas}

            {MENESA_CSS} {{
                visibility: hidden;
            }}
            {menesi}

            div[aria-label="Calendar."] div:has(div[role="gridcell"]) div button:nth-child(2){{
                visibility: hidden;
            }}

            {menesa_izvelne}
        </style>
    """ .format(menesi=MENESU_TULKOJUMS, MENESA_CSS=MENESA_CSS, dienas=DIENAS_TULKOJUMS, dienas_izvele=DIENAS_SAISINAJUMA_CSS, menesa_izvelne=MENESA_IZVELNES_TULKOJUMS)
