import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
import time
import io
import plotly.express as px


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="HydroAgri Nexus",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ADVANCED INTERFACE STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(19, 132, 150, 0.10), transparent 28%),
            radial-gradient(circle at 90% 15%, rgba(25, 118, 210, 0.08), transparent 30%),
            #f4f7fa;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #eef3f7 0%, #e5edf2 100%);
        border-right: 1px solid #d7e1e8;
    }

    [data-testid="stSidebar"] button {
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] button:hover {
        transform: translateX(3px);
        border-color: #168aad;
    }

    .hero-card {
        padding: 34px 36px;
        border-radius: 24px;
        background: linear-gradient(135deg, #082f49 0%, #0b5d66 55%, #168aad 100%);
        color: white;
        box-shadow: 0 18px 45px rgba(8, 47, 73, 0.22);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-card:after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        border-radius: 50%;
        right: -60px;
        top: -80px;
        background: rgba(255,255,255,0.08);
    }

    .hero-kicker {
        font-size: 14px;
        letter-spacing: 2px;
        text-transform: uppercase;
        opacity: 0.78;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 42px;
        line-height: 1.05;
        font-weight: 800;
        margin: 0;
    }

    .hero-subtitle {
        font-size: 17px;
        opacity: 0.90;
        margin-top: 10px;
    }

    .floating-card {
        padding: 22px;
        border-radius: 20px;
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(148,163,184,0.28);
        box-shadow: 0 12px 30px rgba(15,23,42,0.08);
        margin-bottom: 18px;
    }

    .weather-card {
        padding: 26px;
        border-radius: 22px;
        background: linear-gradient(135deg, #ffffff, #eef8fa);
        border: 1px solid #d9e7eb;
        box-shadow: 0 12px 28px rgba(15,23,42,0.07);
        margin-bottom: 20px;
    }

    .weather-location {
        color: #0b3954;
        font-size: 24px;
        font-weight: 750;
    }

    .weather-time {
        color: #64748b;
        font-size: 14px;
        margin-top: 4px;
    }

    .metric-label {
        color: #64748b;
        font-size: 13px;
    }

    .metric-value {
        color: #0b3954;
        font-size: 25px;
        font-weight: 750;
    }

    .section-banner {
        padding: 16px 20px;
        border-radius: 16px;
        background: white;
        border: 1px solid #dbe4ea;
        box-shadow: 0 7px 20px rgba(15,23,42,0.05);
        margin: 14px 0 20px 0;
    }

    .section-banner-title {
        font-size: 25px;
        font-weight: 750;
        color: #0b3954;
    }

    .section-banner-text {
        color: #64748b;
        font-size: 14px;
        margin-top: 3px;
    }
    
        .mini-card {
            padding:18px;
            border-radius:16px;
            background:rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.10);
            line-height:1.6;
        }
</style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# OFFICIAL SOURCES
# ============================================================

FFD_HOME = "https://ffd.pmd.gov.pk/"
FFD_RIVER = "https://ffd.pmd.gov.pk/river-state"
FFD_DASHBOARD = "https://ffd.pmd.gov.pk/flood-dashboard"

WAPDA_RIVER = "https://wapda.gov.pk/river-flow/"
WAPDA_WATER = "https://wapda.gov.pk/water-situation/"

CHRS_DATA = "https://chrsdata.eng.uci.edu/dev/"

# Dashboard weather fallback location
DEFAULT_CITY = "Rawalpindi"
DEFAULT_REGION = "Punjab"
DEFAULT_LAT = 33.5651
DEFAULT_LON = 73.0169
DEFAULT_TZ = "Asia/Karachi"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


def show_startup_splash():
    """Show the launch animation before the sidebar or selected page."""
    if "intro_shown" not in st.session_state:
        st.session_state.intro_shown = False

    if st.session_state.intro_shown:
        return

    st.markdown(
        """<style>
        section[data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .block-container { padding-top: 0 !important; max-width: 100% !important; }
        </style>""",
        unsafe_allow_html=True,
    )

    splash = st.empty()

    splash_content = """
        <style>
        /* Temporarily make the opening screen feel like a separate app launch. */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            display: none !important;
        }
        .block-container {
            padding-top: 0 !important;
            max-width: 100% !important;
        }
    
        .hydro-splash {
            position: relative;
            height: 100vh;
            min-height: 620px;
            margin: -1rem -2rem -2rem -2rem;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                radial-gradient(circle at 50% 25%, rgba(28, 139, 158, .28), transparent 35%),
                linear-gradient(160deg, #03141c 0%, #062b38 48%, #021014 100%);
            color: white;
            font-family: Inter, system-ui, sans-serif;
        }
    
        .hydro-splash::before {
            content: "";
            position: absolute;
            left: -10%;
            right: -10%;
            bottom: -12%;
            height: 44%;
            background: rgba(20, 150, 175, .18);
            border-radius: 50% 50% 0 0 / 22% 22% 0 0;
            animation: hydro-wave 3.2s ease-in-out infinite alternate;
        }
    
        .hydro-splash::after {
            content: "";
            position: absolute;
            left: -15%;
            right: -15%;
            bottom: -18%;
            height: 38%;
            background: rgba(70, 190, 205, .12);
            border-radius: 50% 50% 0 0 / 30% 30% 0 0;
            animation: hydro-wave 4.4s ease-in-out infinite alternate-reverse;
        }
    
        .splash-content {
            position: relative;
            z-index: 5;
            text-align: center;
            padding: 30px;
            animation: splash-in 1.8s ease-out both;
        }
    
        .splash-kicker {
            letter-spacing: .22em;
            text-transform: uppercase;
            font-size: 12px;
            opacity: .72;
            margin-bottom: 18px;
        }
    
        .splash-title {
            font-size: clamp(42px, 7vw, 86px);
            line-height: .95;
            font-weight: 800;
            letter-spacing: -.045em;
            text-shadow: 0 10px 40px rgba(0,0,0,.35);
        }
    
        .splash-subtitle {
            margin-top: 18px;
            font-size: clamp(14px, 2vw, 20px);
            opacity: .82;
            letter-spacing: .04em;
        }
    
        .splash-scene {
            position: relative;
            width: min(440px, 72vw);
            height: 150px;
            margin: 30px auto 0;
        }
    
        .splash-ground {
            position: absolute;
            left: 50%;
            bottom: 18px;
            width: 180px;
            height: 24px;
            transform: translateX(-50%);
            background: rgba(83, 118, 72, .65);
            border-radius: 50%;
            filter: blur(.2px);
        }
    
        .splash-stem {
            position: absolute;
            left: 50%;
            bottom: 35px;
            width: 7px;
            height: 0;
            transform: translateX(-50%);
            border-radius: 8px;
            background: #67b982;
            transform-origin: bottom;
            animation: plant-grow 3.2s 0.5s ease-out forwards;
        }
    
        .splash-leaf {
            position: absolute;
            left: 50%;
            bottom: 88px;
            width: 58px;
            height: 25px;
            opacity: 0;
            background: #6fbe83;
            border-radius: 100% 0 100% 0;
        }
    
        .splash-leaf.left {
            transform: translateX(-95%) rotate(-28deg);
            transform-origin: right bottom;
            animation: leaf-left 2s 2.2s ease-out forwards;
        }
    
        .splash-leaf.right {
            transform: translateX(-5%) rotate(28deg) scaleX(-1);
            transform-origin: left bottom;
            animation: leaf-right 2s 2.5s ease-out forwards;
        }
    
        .splash-river {
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 52px;
            overflow: hidden;
            opacity: .9;
        }
    
        .splash-river-line {
            position: absolute;
            width: 160%;
            height: 18px;
            left: -30%;
            border-top: 3px solid rgba(115, 222, 235, .72);
            border-radius: 50%;
            animation: river-flow 2.2s linear infinite;
        }
    
        .splash-river-line:nth-child(2) {
            top: 19px;
            opacity: .55;
            animation-duration: 3s;
        }
    
        .splash-river-line:nth-child(3) {
            top: 35px;
            opacity: .35;
            animation-duration: 3.8s;
        }
    
        .splash-loading {
            margin-top: 26px;
            font-size: 11px;
            letter-spacing: .16em;
            text-transform: uppercase;
            opacity: .55;
        }
    
        @keyframes splash-in {
            from { opacity: 0; transform: translateY(18px) scale(.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes plant-grow {
            to { height: 82px; }
        }
        @keyframes leaf-left {
            from { opacity: 0; transform: translateX(-95%) rotate(-70deg) scale(.2); }
            to { opacity: 1; transform: translateX(-95%) rotate(-28deg) scale(1); }
        }
        @keyframes leaf-right {
            from { opacity: 0; transform: translateX(-5%) rotate(70deg) scaleX(-1) scale(.2); }
            to { opacity: 1; transform: translateX(-5%) rotate(28deg) scaleX(-1) scale(1); }
        }
        @keyframes river-flow {
            from { transform: translateX(-7%); }
            to { transform: translateX(22%); }
        }
        @keyframes hydro-wave {
            from { transform: translateX(-2%) scaleX(1.02); }
            to { transform: translateX(2%) scaleX(1.08); }
        }
        </style>
    
        <div class="hydro-splash">
            <div class="splash-content">
                <div class="splash-kicker">Pakistan Hydrology & Agricultural Intelligence</div>
                <div class="splash-title">🌊 HydroAgri Nexus</div>
                <div class="splash-subtitle">Water • Climate • Crops • Scientific Intelligence</div>
    
                <div class="splash-scene">
                    <div class="splash-ground"></div>
                    <div class="splash-stem"></div>
                    <div class="splash-leaf left"></div>
                    <div class="splash-leaf right"></div>
                    <div class="splash-river">
                        <div class="splash-river-line"></div>
                        <div class="splash-river-line"></div>
                        <div class="splash-river-line"></div>
                    </div>
                </div>
    
                <div class="splash-loading">Initializing hydro-agricultural intelligence</div>
            </div>
        </div>
        """

    with splash.container():
        components.html(
            splash_content,
            height=760,
            scrolling=False,
        )

    time.sleep(7.0)
    st.session_state.intro_shown = True
    splash.empty()

    st.markdown(
        """<style>
        section[data-testid="stSidebar"] { display: block !important; }
        header[data-testid="stHeader"] { display: flex !important; }
        </style>""",
        unsafe_allow_html=True,
    )


# ============================================================
# LIVE FFD DATA FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def fetch_ffd_home():
    """
    Fetch official FFD homepage.

    Cache = 5 minutes.
    This prevents excessive requests while keeping
    the dashboard reasonably current.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/151.0 Safari/537.36"
        )
    }

    response = requests.get(
        FFD_HOME,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    return response.text


def clean_html_text(html):
    """
    Basic HTML-to-text conversion without BeautifulSoup.
    """

    text = re.sub(
        r"<script.*?</script>",
        " ",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    text = re.sub(
        r"<style.*?</style>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def extract_ffd_update(text):
    """
    Extract the latest FFD update timestamp.
    """

    patterns = [
        r"Updated\s+(\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}\s+PKT)",
        r"Updated\s+(\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return "Not detected"


def extract_river_status(text):
    """
    Extract current river status from FFD homepage.

    Expected structure:

    Indus ... Below Low
    Kabul ... Below Low
    etc.
    """

    rivers = [
        "Indus",
        "Kabul",
        "Jhelum",
        "Neelum",
        "Chenab",
        "Ravi",
        "Sutlej",
    ]

    statuses = [
        "Exceptionally High",
        "Very High",
        "High",
        "Medium",
        "Low",
        "Below Low",
        "Normal Flow",
    ]

    records = []

    for river in rivers:

        river_pattern = re.escape(river)

        found_status = None

        for status in statuses:

            pattern = (
                river_pattern
                + r".{0,100}?"
                + re.escape(status)
            )

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                found_status = status
                break

        if found_status is None:
            found_status = "Not detected"

        records.append(
            {
                "River": river,
                "Current Status": found_status,
            }
        )

    return pd.DataFrame(records)


def status_type(status):

    status = status.lower()

    if "exceptionally" in status:
        return "🔴 Exceptionally High"

    if "very high" in status:
        return "🔴 Very High"

    if status == "high":
        return "🟠 High"

    if "medium" in status:
        return "🟡 Medium"

    if status == "low":
        return "🟡 Low"

    if "below low" in status:
        return "🟢 Below Low"

    if "normal" in status:
        return "🟢 Normal"

    return "⚪ Unknown"


# ============================================================
# EXTRACT CURRENT WEATHER FROM FFD
# ============================================================

def extract_city_weather(text, city_name):

    """
    Extract current PMD/FFD weather information
    from the official FFD homepage.

    The FFD homepage publishes weather observations
    for many Pakistani locations.
    """

    escaped_city = re.escape(city_name)

    pattern = (
        escaped_city
        + r".{0,300}?"
        + r"(\d+(?:\.\d+)?)°"
        + r".{0,150}?"
        + r"(\d+(?:\.\d+)?)\s*mm"
        + r".{0,100}?"
        + r"(\d+(?:\.\d+)?)\s*kt"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return {
        "City": city_name,
        "Temperature": float(match.group(1)),
        "Rainfall": float(match.group(2)),
        "Wind": float(match.group(3)),
    }




# ============================================================
# DASHBOARD WEATHER
# ============================================================

@st.cache_data(ttl=300)
def fetch_dashboard_weather():
    """
    Dashboard weather uses Rawalpindi as the reliable Pakistan
    fallback. It does not depend on ipapi.co.
    """

    params = {
        "latitude": DEFAULT_LAT,
        "longitude": DEFAULT_LON,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum"
        ),
        "timezone": DEFAULT_TZ,
        "forecast_days": 1
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=12
    )
    response.raise_for_status()
    return response.json()


def weather_text(code):
    codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return codes.get(code, "Current conditions")


# ============================================================
# HYDROLOGY CALCULATIONS
# ============================================================

def scs_cn(P, CN):

    S = 25400 / CN - 254

    Ia = 0.2 * S

    if P <= Ia:
        Q = 0
    else:
        Q = ((P - Ia) ** 2) / (P + 0.8 * S)

    return S, Ia, Q


def rational_method(C, intensity, area):

    return 0.278 * C * intensity * area


def gumbel_frequency(data, T):

    data = np.asarray(data, dtype=float)

    mean = np.mean(data)

    std = np.std(
        data,
        ddof=1,
    )

    y = -np.log(
        -np.log(
            1 - 1 / T
        )
    )

    gamma = 0.5772156649

    K = (
        y - gamma
    ) / (
        np.pi / np.sqrt(6)
    )

    return mean + K * std


# ============================================================
# FAO-56
# ============================================================

def fao56_et0(
    tmean,
    tmax,
    tmin,
    rh,
    wind,
    rn,
    pressure,
):

    es_tmax = (
        0.6108
        * np.exp(
            17.27 * tmax
            / (tmax + 237.3)
        )
    )

    es_tmin = (
        0.6108
        * np.exp(
            17.27 * tmin
            / (tmin + 237.3)
        )
    )

    es = (
        es_tmax
        + es_tmin
    ) / 2

    ea = es * rh / 100

    delta = (
        4098
        * (
            0.6108
            * np.exp(
                17.27 * tmean
                / (tmean + 237.3)
            )
        )
        / (
            (tmean + 237.3) ** 2
        )
    )

    gamma = (
        0.000665
        * pressure
    )

    G = 0

    numerator = (
        0.408
        * delta
        * (rn - G)
        +
        gamma
        * (
            900
            / (tmean + 273)
        )
        * wind
        * (es - ea)
    )

    denominator = (
        delta
        +
        gamma
        * (
            1
            + 0.34 * wind
        )
    )

    if denominator == 0:
        return 0

    return max(
        numerator / denominator,
        0,
    )



show_startup_splash()

# ============================================================
# CATCHY SUBSECTION CARD NAVIGATION
# ============================================================

st.markdown(
    """<style>
    /* Modern HydroAgri subsection cards */
    div[data-testid="stButton"] > button {
        min-height: 92px !important;
        width: 100% !important;
        border-radius: 18px !important;
        border: 1px solid rgba(22, 143, 138, 0.20) !important;
        background: linear-gradient(145deg, #ffffff 0%, #f3faf9 100%) !important;
        color: #12384a !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        line-height: 1.35 !important;
        padding: 15px 12px !important;
        box-shadow: 0 7px 20px rgba(16, 67, 85, 0.09) !important;
        transition: all 0.18s ease-in-out !important;
    }

    div[data-testid="stButton"] > button:hover {
        transform: translateY(-4px) !important;
        border-color: #168f8a !important;
        box-shadow: 0 12px 28px rgba(13, 92, 104, 0.18) !important;
        color: #0b6867 !important;
    }

    div[data-testid="stButton"] > button:active {
        transform: translateY(-1px) !important;
    }

    /* Primary button = selected subsection card */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #0b5967 0%, #159a91 100%) !important;
        border-color: #0b5967 !important;
        color: #ffffff !important;
        box-shadow: 0 12px 30px rgba(11, 89, 103, 0.28) !important;
    }

    div[data-testid="stButton"] > button[kind="primary"]:hover {
        color: #ffffff !important;
        filter: brightness(1.04);
    }

    /* Space around each row of cards */
    div[data-testid="stHorizontalBlock"] {
        gap: 14px !important;
    }

    .hydro-section-caption {
        color: #6a7d89;
        font-size: 0.88rem;
        margin: -5px 0 16px 2px;
    }

    .hydro-section-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #12384a;
        margin: 4px 0 10px 2px;
    }
    </style>""",
    unsafe_allow_html=True,
)

def subsection_cards(section_key, items):
    """Render attractive clickable subsection cards and return selected index."""
    state_key = f"selected_subsection_{section_key}"

    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    for row_start in range(0, len(items), 4):
        row_items = items[row_start:row_start + 4]
        cols = st.columns(4)

        for offset, item in enumerate(row_items):
            idx = row_start + offset
            with cols[offset]:
                selected = st.session_state[state_key] == idx
                if st.button(
                    item["label"],
                    key=f"{section_key}_subsection_{idx}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state[state_key] = idx
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    selected_index = st.session_state[state_key]
    st.markdown(
        f"<div class='hydro-section-caption'>"
        f"Selected: <b>{items[selected_index]['title']}</b> — "
        f"{items[selected_index]['description']}</div>",
        unsafe_allow_html=True,
    )
    return selected_index


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 🌊 HydroAgri Nexus"
    )
    st.caption("Pakistan Hydrology & Agricultural Intelligence")

    st.caption(
        "Pakistan Hydrology & Agricultural Intelligence"
    )

    st.divider()

    pages = [
        "Dashboard",
        "🌧️ Hydrology",
        "☀️ Evapotranspiration",
        "🇵🇰 Live Pakistan Water",
        "🌱 Crop & Climate",
        "📊 Data Analysis",
    ]

    for page in pages:

        if st.button(
            page,
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.page == page
                else "secondary"
            ),
        ):

            st.session_state.page = page

            st.rerun()

    st.divider()

    st.subheader("Live Sources")

    st.link_button(
        "FFD Live Rivers",
        FFD_RIVER,
        use_container_width=True,
    )

    st.link_button(
        "FFD Flood Dashboard",
        FFD_DASHBOARD,
        use_container_width=True,
    )

    st.link_button(
        "WAPDA River Flow",
        WAPDA_RIVER,
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "Live refresh interval: 5 minutes"
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    # Current local time
    now = datetime.now(ZoneInfo(DEFAULT_TZ))

    try:
        weather = fetch_dashboard_weather()
        current = weather["current"]
        daily = weather["daily"]

        temperature = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        rainfall = current.get("precipitation")
        wind = current.get("wind_speed_10m")
        condition = weather_text(current.get("weather_code"))

        max_temp = daily["temperature_2m_max"][0]
        min_temp = daily["temperature_2m_min"][0]
        rain_today = daily["precipitation_sum"][0]

        st.markdown(
            '<div class="section-banner">'
            '<div class="section-banner-title">🌤️ Live Dashboard Weather</div>'
            '<div class="section-banner-text">'
            'Current atmospheric conditions for the default Pakistan location.'
            '</div></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="weather-card">'
            f'<div class="weather-location">📍 {DEFAULT_CITY}, {DEFAULT_REGION}, Pakistan</div>'
            f'<div class="weather-time">🕒 {now.strftime("%A, %d %B %Y • %I:%M:%S %p")} PKT</div>'
            '</div>',
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("🌡️ Temperature", f"{temperature:.1f} °C")

        with c2:
            st.metric("💧 Humidity", f"{humidity:.0f} %")

        with c3:
            st.metric("🌧️ Rain Today", f"{rain_today:.1f} mm")

        with c4:
            st.metric("💨 Wind", f"{wind:.1f} km/h")

        st.info(
            f"Current condition: **{condition}**  •  "
            f"Feels like **{feels_like:.1f} °C**  •  "
            f"Today's range: **{min_temp:.1f}–{max_temp:.1f} °C**"
        )

        st.caption(
            "Weather service: Open-Meteo. Location fallback: Rawalpindi, Punjab, Pakistan. "
            "The Dashboard does not depend on IP geolocation."
        )

    except Exception:
        st.warning(
            "Live weather is temporarily unavailable. "
            "The application interface is still running normally."
        )

        st.markdown(
            f"""
            <div class="floating-card">
                <b>📍 Location:</b> {DEFAULT_CITY}, {DEFAULT_REGION}, Pakistan<br>
                <b>🕒 Pakistan Time:</b> {now.strftime("%A, %d %B %Y • %I:%M:%S %p")} PKT
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown(
        """
        <div class="floating-card">
            <b>HydroAgri Nexus</b><br>
            An integrated scientific platform for rainfall-runoff analysis,
            evapotranspiration, crop water requirements, hydrological
            frequency analysis, and Pakistan water-resource monitoring.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# LIVE PAKISTAN WATER
# ============================================================

def live_pakistan_water():

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Official Pakistan Water Monitoring</div>
            <div class="hero-title">🇵🇰 Live Pakistan Water</div>
            <div class="hero-subtitle">
                Flood Forecasting Division / PMD and WAPDA information
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        html = fetch_ffd_home()
        text = clean_html_text(html)
        update_time = extract_ffd_update(text)
        river_df = extract_river_status(text)

        st.success("FFD / PMD connection: ONLINE")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Connection", "ONLINE")
        with c2:
            st.metric("FFD Update", update_time)
        with c3:
            st.metric("Rivers Monitored", len(river_df))

        st.markdown("### 🌊 Current River Status")

        display_df = river_df.copy()
        display_df["Status"] = display_df["Current Status"].apply(status_type)

        st.dataframe(
            display_df[["River", "Status"]],
            use_container_width=True,
            hide_index=True
        )

    except Exception as error:
        st.error("Could not connect to the official FFD website.")
        st.caption(str(error))

    st.markdown("### 🔗 Official Live Sources")

    a, b, c = st.columns(3)

    with a:
        st.link_button(
            "🌊 FFD Live River Gauge Map",
            FFD_RIVER,
            use_container_width=True
        )

    with b:
        st.link_button(
            "📊 FFD Flood Dashboard",
            FFD_DASHBOARD,
            use_container_width=True
        )

    with c:
        st.link_button(
            "💧 WAPDA River Flow",
            WAPDA_RIVER,
            use_container_width=True
        )

    st.caption(
        "Individual gauge discharge values should be taken from the official "
        "FFD live map/discharge reporting rather than fabricated by the application."
    )


# ============================================================
# HYDROLOGY
# ============================================================

def hydrology():

    st.title("🌧️ Hydrology")

    selected = subsection_cards(
        "hydrology",
        [
            {"label": "🌧️  Rainfall\nAnalysis", "title": "Rainfall Analysis", "description": "Rainfall statistics and event-depth exploration."},
            {"label": "📈  Frequency\nAnalysis", "title": "Frequency Analysis", "description": "Return-period and extreme rainfall analysis."},
            {"label": "📊  IDF\nCurves", "title": "IDF Curves", "description": "Intensity-duration-frequency analysis."},
            {"label": "💧  SCS-CN\nRunoff", "title": "SCS-CN Runoff", "description": "Curve-number based direct runoff estimation."},
            {"label": "⚡  Rational\nMethod", "title": "Rational Method", "description": "Peak discharge estimation for catchments."},
            {"label": "🌧️  Hyetograph\nAnalysis", "title": "Hyetograph Analysis", "description": "Time-based rainfall intensity using manual or Excel data."},
            {"label": "🌊  Hydrograph\nAnalysis", "title": "Hydrograph Analysis", "description": "Time-based streamflow response using manual or Excel data."},
            {"label": "⚖️  Water\nBalance", "title": "Water Balance", "description": "Catchment water-balance components."},
        ],
    )

    def _normalise_columns(df):
        clean = {}
        for col in df.columns:
            key = re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
            clean[key] = col
        return clean

    def _find_column(df, candidates):
        mapping = _normalise_columns(df)
        normalised = [re.sub(r"[^a-z0-9]+", "_", c.lower()).strip("_") for c in candidates]
        for candidate in normalised:
            if candidate in mapping:
                return mapping[candidate]
        for key, original in mapping.items():
            if any(candidate in key for candidate in normalised):
                return original
        return None

    def _load_timeseries(uploaded, value_candidates, value_label):
        try:
            if uploaded.name.lower().endswith(".csv"):
                raw = pd.read_csv(uploaded)
            else:
                raw = pd.read_excel(uploaded)
        except Exception as exc:
            return None, f"Could not read the file: {exc}"

        time_col = _find_column(raw, ["time", "datetime", "date_time", "date", "timestamp"])
        value_col = _find_column(raw, value_candidates)

        if time_col is None:
            return None, "No Time/DateTime column was detected. Add a column named Time, DateTime, Date or Timestamp."
        if value_col is None:
            return None, f"No {value_label} column was detected."

        parsed_time = pd.to_datetime(raw[time_col], errors="coerce")
        values = pd.to_numeric(raw[value_col], errors="coerce")
        invalid_time = int(parsed_time.isna().sum())
        invalid_values = int(values.isna().sum())

        df = pd.DataFrame({"Time": parsed_time, value_label: values}).dropna()
        if len(df) < 2:
            return None, "At least two valid time-value observations are required."
        if df["Time"].duplicated().any():
            return None, "Duplicate timestamps were found. The X-axis must contain unique times."
        df = df.sort_values("Time").reset_index(drop=True)
        intervals = df["Time"].diff().dt.total_seconds() / 60.0
        if (intervals.iloc[1:] <= 0).any():
            return None, "Time values must increase chronologically with positive intervals."
        df.attrs["source_info"] = f"Detected X-axis: {time_col} | Y-axis: {value_col} | Invalid time rows: {invalid_time} | Invalid value rows: {invalid_values}"
        return df, None

    # --------------------------------------------------------
    # RAINFALL
    # --------------------------------------------------------
    if selected == 0:
        st.header("Rainfall Analysis")
        values = st.text_area("Rainfall values (mm)", "120,145,98,175,190,132,165,210,185,225")
        try:
            data = np.array([float(x.strip()) for x in values.split(",") if x.strip()])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", f"{np.mean(data):.2f} mm", border=True)
            c2.metric("Maximum", f"{np.max(data):.2f} mm", border=True)
            c3.metric("Minimum", f"{np.min(data):.2f} mm", border=True)
            c4.metric("Std Dev", f"{np.std(data, ddof=1):.2f} mm", border=True)
            chart = pd.DataFrame({"Observation": np.arange(1, len(data)+1), "Rainfall (mm)": data})
            st.line_chart(chart.set_index("Observation"))
        except Exception:
            st.error("Enter valid numerical values.")

    # --------------------------------------------------------
    # FREQUENCY
    # --------------------------------------------------------
    if selected == 1:
        st.header("Gumbel Frequency Analysis")
        values = st.text_area("Annual maximum rainfall (mm)", "120,145,155,132,178,190,165,201,220,185,240,215")
        T = st.selectbox("Return period", [2, 5, 10, 25, 50, 100])
        try:
            data = np.array([float(x.strip()) for x in values.split(",") if x.strip()])
            result = gumbel_frequency(data, T)
            st.metric(f"{T}-year rainfall", f"{result:.2f} mm", border=True)
        except Exception:
            st.error("Enter valid numerical data.")

    # --------------------------------------------------------
    # IDF
    # --------------------------------------------------------
    if selected == 2:
        st.header("IDF Calculation")
        durations = st.text_input("Duration (minutes)", "15,30,60,120")
        depths = st.text_input("Rainfall depth (mm)", "35,52,75,100")
        try:
            d = np.array([float(x.strip()) for x in durations.split(",")])
            p = np.array([float(x.strip()) for x in depths.split(",")])
            if len(d) != len(p) or np.any(d <= 0):
                raise ValueError
            intensity = p / d * 60
            idf = pd.DataFrame({"Duration (min)": d, "Depth (mm)": p, "Intensity (mm/hr)": intensity})
            st.dataframe(idf, use_container_width=True, hide_index=True)
            st.line_chart(idf.set_index("Duration (min)")["Intensity (mm/hr)"])
        except Exception:
            st.error("Enter matching positive numerical values.")

    # --------------------------------------------------------
    # SCS CN
    # --------------------------------------------------------
    if selected == 3:
        st.header("SCS Curve Number")
        P = st.number_input("Rainfall P (mm)", 0.0, 1000.0, 100.0)
        CN = st.number_input("Curve Number", 1.0, 99.0, 75.0)
        S, Ia, Q = scs_cn(P, CN)
        c1, c2, c3 = st.columns(3)
        c1.metric("S", f"{S:.2f} mm", border=True)
        c2.metric("Ia", f"{Ia:.2f} mm", border=True)
        c3.metric("Runoff", f"{Q:.2f} mm", border=True)
        st.latex(r"S=\frac{25400}{CN}-254")
        st.latex(r"Q=\frac{(P-I_a)^2}{P+0.8S}")

    # --------------------------------------------------------
    # RATIONAL
    # --------------------------------------------------------
    if selected == 4:
        st.header("Rational Method")
        C = st.number_input("Runoff coefficient C", 0.0, 1.0, 0.6)
        intensity = st.number_input("Rainfall intensity (mm/hr)", 0.0, 1000.0, 50.0)
        area = st.number_input("Catchment area (km²)", 0.01, 100000.0, 10.0)
        Qp = rational_method(C, intensity, area)
        st.metric("Peak discharge", f"{Qp:.3f} m³/s", border=True)
        st.latex(r"Q_p=0.278CIA")

    # --------------------------------------------------------
    # HYETOGRAPH
    # --------------------------------------------------------
    if selected == 5:
        st.header("🌧️ Hyetograph Analysis")
        st.markdown("""
        <div class="glass-card" style="padding:20px; margin-bottom:18px;">
            <b>Hyetograph convention</b><br>
            <b>X-axis = actual Time/DateTime</b> and <b>Y-axis = rainfall intensity (mm/hr)</b>.
            You can enter observations manually or upload Excel/CSV data.
        </div>
        """, unsafe_allow_html=True)

        source = st.radio("Data source", ["✍️ Manual Data", "📗 Excel / CSV Upload"], horizontal=True, key="hyetograph_source")
        mode = st.selectbox("Rainfall input", ["Rainfall depth per interval (mm)", "Rainfall intensity (mm/hr)"], key="hyetograph_mode")

        if source.startswith("✍️"):
            default = pd.DataFrame({
                "Time": pd.date_range("2026-01-01 00:00", periods=12, freq="1h"),
                "Rainfall": [0, 2, 5, 12, 20, 15, 8, 4, 2, 1, 0, 0],
            })
            edited = st.data_editor(default, num_rows="dynamic", use_container_width=True,
                column_config={
                    "Time": st.column_config.DatetimeColumn("Time (X-axis)", format="YYYY-MM-DD HH:mm"),
                    "Rainfall": st.column_config.NumberColumn("Rainfall", min_value=0.0, format="%.3f"),
                }, key="hyetograph_manual_editor")
            df = edited.copy()
            df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
            df["Rainfall"] = pd.to_numeric(df["Rainfall"], errors="coerce")
            df = df.dropna().sort_values("Time").reset_index(drop=True)
            if len(df) >= 2 and df["Time"].duplicated().any():
                st.error("Duplicate timestamps detected. Please use unique Time values.")
                df = None
        else:
            uploaded = st.file_uploader("Upload Excel (.xlsx/.xls) or CSV", type=["xlsx", "xls", "csv"], key="hyetograph_file")
            df = None
            if uploaded is not None:
                df, error = _load_timeseries(uploaded, ["rainfall", "rain", "precipitation", "precip", "rainfall_mm", "rain_mm"], "Rainfall")
                if error:
                    st.error(error)
                else:
                    st.caption(df.attrs.get("source_info", ""))

        if df is not None and len(df) >= 2:
            df["Rainfall"] = pd.to_numeric(df["Rainfall"], errors="coerce")
            df = df.dropna(subset=["Time", "Rainfall"]).copy()
            if (df["Rainfall"] < 0).any():
                st.error("Rainfall values cannot be negative.")
            else:
                intervals = df["Time"].diff().dt.total_seconds() / 3600.0
                positive = intervals.iloc[1:][intervals.iloc[1:] > 0]
                if mode.startswith("Rainfall depth"):
                    if len(positive) == 0:
                        st.error("Positive time intervals are required to calculate intensity.")
                        intensity_ok = False
                    else:
                        first_interval = float(positive.median())
                        intervals.iloc[0] = first_interval
                        df["Intensity (mm/hr)"] = df["Rainfall"] / intervals * 1.0
                        intensity_ok = True
                else:
                    df["Intensity (mm/hr)"] = df["Rainfall"]
                    intensity_ok = True

                if intensity_ok:
                    st.success("✓ X-axis verified as chronological Time/DateTime. Y-axis is rainfall intensity (mm/hr).")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total rainfall", f"{df['Rainfall'].sum():.2f} mm", border=True)
                    c2.metric("Maximum intensity", f"{df['Intensity (mm/hr)'].max():.2f} mm/hr", border=True)
                    c3.metric("Observations", len(df), border=True)
                    fig = px.bar(df, x="Time", y="Intensity (mm/hr)", title="Rainfall Hyetograph",
                                 labels={"Time":"Time", "Intensity (mm/hr)":"Rainfall intensity (mm/hr)"})
                    fig.update_layout(height=480, xaxis_title="Time", yaxis_title="Rainfall intensity (mm/hr)", bargap=0.08, hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(df[["Time", "Rainfall", "Intensity (mm/hr)"]], use_container_width=True, hide_index=True)

    # --------------------------------------------------------
    # HYDROGRAPH
    # --------------------------------------------------------
    if selected == 6:
        st.header("🌊 Hydrograph Analysis")
        st.markdown("""
        <div class="glass-card" style="padding:20px; margin-bottom:18px;">
            <b>Hydrograph convention</b><br>
            <b>X-axis = actual Time/DateTime</b> and <b>Y-axis = discharge (m³/s)</b>.
            Enter observations manually or upload Excel/CSV data.
        </div>
        """, unsafe_allow_html=True)

        source = st.radio("Data source", ["✍️ Manual Data", "📗 Excel / CSV Upload"], horizontal=True, key="hydrograph_source")

        if source.startswith("✍️"):
            default = pd.DataFrame({
                "Time": pd.date_range("2026-01-01 00:00", periods=12, freq="1h"),
                "Discharge": [10, 12, 15, 25, 40, 65, 90, 75, 50, 32, 20, 14],
            })
            edited = st.data_editor(default, num_rows="dynamic", use_container_width=True,
                column_config={
                    "Time": st.column_config.DatetimeColumn("Time (X-axis)", format="YYYY-MM-DD HH:mm"),
                    "Discharge": st.column_config.NumberColumn("Discharge (m³/s)", min_value=0.0, format="%.3f"),
                }, key="hydrograph_manual_editor")
            df = edited.copy()
            df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
            df["Discharge"] = pd.to_numeric(df["Discharge"], errors="coerce")
            df = df.dropna().sort_values("Time").reset_index(drop=True)
            if len(df) >= 2 and df["Time"].duplicated().any():
                st.error("Duplicate timestamps detected. Please use unique Time values.")
                df = None
        else:
            uploaded = st.file_uploader("Upload Excel (.xlsx/.xls) or CSV", type=["xlsx", "xls", "csv"], key="hydrograph_file")
            df = None
            if uploaded is not None:
                df, error = _load_timeseries(uploaded, ["discharge", "flow", "streamflow", "q", "discharge_m3_s", "flow_m3_s"], "Discharge")
                if error:
                    st.error(error)
                else:
                    st.caption(df.attrs.get("source_info", ""))

        if df is not None and len(df) >= 2:
            df["Discharge"] = pd.to_numeric(df["Discharge"], errors="coerce")
            df = df.dropna(subset=["Time", "Discharge"]).copy()
            if (df["Discharge"] < 0).any():
                st.error("Discharge values cannot be negative.")
            else:
                peak_idx = int(df["Discharge"].idxmax())
                peak = float(df.loc[peak_idx, "Discharge"])
                peak_time = df.loc[peak_idx, "Time"]
                mean_q = float(df["Discharge"].mean())
                st.success("✓ X-axis verified as chronological Time/DateTime. Y-axis is discharge (m³/s).")
                c1, c2, c3 = st.columns(3)
                c1.metric("Peak discharge", f"{peak:.2f} m³/s", border=True)
                c2.metric("Time of peak", peak_time.strftime("%Y-%m-%d %H:%M"), border=True)
                c3.metric("Mean discharge", f"{mean_q:.2f} m³/s", border=True)
                fig = px.line(df, x="Time", y="Discharge", markers=True, title="Streamflow Hydrograph",
                              labels={"Time":"Time", "Discharge":"Discharge (m³/s)"})
                fig.update_layout(height=480, xaxis_title="Time", yaxis_title="Discharge (m³/s)", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[["Time", "Discharge"]], use_container_width=True, hide_index=True)

    # --------------------------------------------------------
    # WATER BALANCE
    # --------------------------------------------------------
    if selected == 7:
        st.header("Water Balance")
        P = st.number_input("Precipitation P", 0.0, 10000.0, 100.0)
        I = st.number_input("Irrigation I", 0.0, 10000.0, 20.0)
        G = st.number_input("Groundwater G", 0.0, 10000.0, 5.0)
        R = st.number_input("Runoff R", 0.0, 10000.0, 25.0)
        ET = st.number_input("ET", 0.0, 10000.0, 50.0)
        D = st.number_input("Drainage D", 0.0, 10000.0, 10.0)
        storage = P + I + G - R - ET - D
        st.metric("ΔS", f"{storage:.2f} mm", border=True)
        st.latex(r"\Delta S=P+I+G-R-ET-D")


# ============================================================
# EVAPOTRANSPIRATION
# ============================================================

def evapotranspiration():

    st.title("☀️ Evapotranspiration")

    selected = subsection_cards(
        "evapotranspiration",
        [
            {"label": "☀️  FAO-56\nET₀", "title": "FAO-56 Reference ET₀", "description": "Penman–Monteith reference evapotranspiration."},
            {"label": "🌱  Crop\nET", "title": "Crop ET", "description": "Estimate crop evapotranspiration from Kc."},
            {"label": "🌤️  Climate\nInputs", "title": "Climate Inputs", "description": "Temperature, humidity, wind and radiation drivers."},
            {"label": "💧  Water\nRequirement", "title": "Water Requirement", "description": "Translate crop demand into irrigation requirement."},
        ],
    )

    if selected == 0:
        st.header("FAO-56 Penman–Monteith")

        c1, c2, c3 = st.columns(3)

        with c1:
            Tmean = st.number_input("Mean temperature °C", 25.0)
            Tmax = st.number_input("Maximum temperature °C", 32.0)
            Tmin = st.number_input("Minimum temperature °C", 18.0)

        with c2:
            RH = st.number_input("Relative humidity %", 55.0)
            wind = st.number_input("Wind speed m/s", 2.0)

        with c3:
            Rn = st.number_input("Net radiation MJ/m²/day", 15.0)
            pressure = st.number_input("Pressure kPa", 90.0)

        ET0 = fao56_et0(Tmean, Tmax, Tmin, RH, wind, Rn, pressure)
        st.metric("Reference ET₀", f"{ET0:.2f} mm/day", border=True)
        st.latex(r"""ET_0=\frac{0.408\Delta(R_n-G)+\gamma\frac{900}{T+273}u_2(e_s-e_a)}{\Delta+\gamma(1+0.34u_2)}""")

    if selected == 1:
        st.subheader("🌱 Crop Evapotranspiration")
        st.info("Use the Crop & Climate module for crop-specific Kc and ETc calculations.")
        st.page_link("#", label="🌱 Crop & Climate module", icon="🌱") if False else None

    if selected == 2:
        st.subheader("🌤️ Climate Inputs")
        st.write("Key climate drivers for ET₀ include temperature, humidity, wind speed, radiation and atmospheric pressure.")
        st.caption("These inputs feed the FAO-56 Penman–Monteith calculation above.")

    if selected == 3:
        st.subheader("💧 Agricultural Water Requirement")
        st.info("Crop water requirement can be developed from ET₀ × Kc and effective rainfall in the Crop & Climate module.")


# ============================================================
# CROP & CLIMATE
# ============================================================

def crop_climate():

    st.title("🌱 Crop & Climate")

    selected = subsection_cards(
        "crop_climate",
        [
            {"label": "🌱  Crop\nET", "title": "Crop Evapotranspiration", "description": "Crop-specific ETc using Kc."},
            {"label": "🌦️  Climate\nIntelligence", "title": "Climate Intelligence", "description": "Climate variables and agricultural interpretation."},
            {"label": "💧  Water\nRequirement", "title": "Crop Water Requirement", "description": "Net water requirement after effective rainfall."},
            {"label": "📅  Growth\nStage", "title": "Growth Stage", "description": "Stage-specific crop coefficients and scheduling."},
        ],
    )

    if selected == 0:
        st.header("Crop Evapotranspiration")
        crop = st.selectbox("Crop", ["Wheat", "Maize", "Rice", "Cotton", "Sugarcane"])
        kc_values = {"Wheat": 1.15, "Maize": 1.20, "Rice": 1.20, "Cotton": 1.15, "Sugarcane": 1.25}
        ET0 = st.number_input("ET₀ (mm/day)", 0.0, 20.0, 5.0)
        Kc = kc_values[crop]
        ETc = ET0 * Kc
        c1, c2 = st.columns(2)
        c1.metric("Crop", crop, border=True)
        c2.metric("ETc", f"{ETc:.2f} mm/day", border=True)
        st.latex(r"ET_c=K_cET_0")

    if selected == 1:
        st.subheader("🌦️ Climate Intelligence")
        st.write("Assess temperature, rainfall, humidity and other climate variables alongside crop water demand.")
        st.info("Climate-data analysis can be connected to uploaded CSV records in Data Analysis.")

    if selected == 2:
        st.subheader("💧 Crop Water Requirement")
        ETc = st.number_input("Crop ETc (mm/day)", 0.0, 30.0, 6.0)
        effective_rain = st.number_input("Effective rainfall (mm/day)", 0.0, 30.0, 1.0)
        net_requirement = max(ETc - effective_rain, 0.0)
        st.metric("Net irrigation requirement", f"{net_requirement:.2f} mm/day", border=True)
        st.latex(r"I_n=ET_c-P_{eff}")

    if selected == 3:
        st.subheader("📅 Crop Growth Stage")
        st.write("Organize Kc and water-demand assumptions by establishment, development, mid-season and late-season stages.")
        st.info("Stage-specific Kc scheduling can be added here as the next scientific module.")


# ============================================================
# DATA ANALYSIS
# ============================================================

def data_analysis():

    st.title("📊 Data Analysis")

    selected = subsection_cards(
        "data_analysis",
        [
            {"label": "📁  Upload\nData", "title": "Upload Data", "description": "Import rainfall, discharge, ET or climate records."},
            {"label": "📈  Statistics", "title": "Statistical Summary", "description": "Descriptive statistics and variability."},
            {"label": "📉  Visualization", "title": "Visualization", "description": "Explore trends and hydrologic time series."},
            {"label": "🔎  Data\nQuality", "title": "Data Quality", "description": "Missing, duplicate and inconsistent record checks."},
            {"label": "📗  Excel\nChart", "title": "Excel Chart Builder", "description": "Upload Excel/CSV and build a polished X-Y chart with axis validation."},
        ],
    )

    if selected == 0:
        file = st.file_uploader("Upload CSV", type=["csv"], key="analysis_csv_upload")
        if file is None:
            st.info("Upload rainfall, discharge, ET or climate CSV data.")
            return
        try:
            df = pd.read_csv(file)
            st.dataframe(df, use_container_width=True)
            st.subheader("Quick Statistics")
            st.dataframe(df.describe(include="all").transpose(), use_container_width=True)
        except Exception as error:
            st.error("Could not read this CSV.")
            st.exception(error)

    if selected == 1:
        st.subheader("📈 Statistical Summary")
        st.write("Upload a dataset in the Upload Data subsection to inspect descriptive statistics, variability and distributions.")

    if selected == 2:
        st.subheader("📉 Visualization")
        st.write("Use uploaded hydrology, rainfall, discharge or climate records to build time-series and comparison charts.")

    if selected == 3:
        st.subheader("🔎 Data Quality")
        st.write("Check missing values, duplicated records, invalid values and inconsistent time-series fields before analysis.")

    if selected == 4:
        st.subheader("📗 Excel / CSV Chart Builder")
        st.markdown("""
        <div class="glass-card" style="padding:20px; margin-bottom:18px;">
            <b>Scientific chart check</b><br>
            Upload an Excel or CSV file, select the X and Y columns, and the application
            will verify that the selected X-axis is numeric or DateTime before plotting.
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload Excel (.xlsx/.xls) or CSV", type=["xlsx", "xls", "csv"], key="excel_chart_upload")
        if uploaded is None:
            st.info("Recommended format: first column = Time/Date, second column = rainfall or discharge.")
            return

        try:
            if uploaded.name.lower().endswith(".csv"):
                chart_df = pd.read_csv(uploaded)
            else:
                chart_df = pd.read_excel(uploaded)
        except Exception as exc:
            st.error(f"Could not read the file: {exc}")
            return

        if chart_df.shape[1] < 2:
            st.error("The file must contain at least two columns.")
            return

        st.caption(f"Loaded {len(chart_df)} rows and {len(chart_df.columns)} columns.")
        st.dataframe(chart_df.head(20), use_container_width=True, hide_index=True)

        x_col = st.selectbox("X-axis column", list(chart_df.columns), key="excel_chart_x")
        y_options = [c for c in chart_df.columns if c != x_col]
        y_col = st.selectbox("Y-axis column", y_options, key="excel_chart_y")
        chart_type = st.selectbox("Chart type", ["Line", "Bar", "Scatter"], key="excel_chart_type")

        x_dt = pd.to_datetime(chart_df[x_col], errors="coerce")
        y_num = pd.to_numeric(chart_df[y_col], errors="coerce")
        datetime_valid = x_dt.notna().sum() >= max(2, int(len(chart_df) * 0.8))
        numeric_valid = pd.to_numeric(chart_df[x_col], errors="coerce").notna().sum() >= max(2, int(len(chart_df) * 0.8))

        if datetime_valid:
            plot_x = x_dt
            x_type = "DateTime"
        elif numeric_valid:
            plot_x = pd.to_numeric(chart_df[x_col], errors="coerce")
            x_type = "Numeric"
        else:
            st.error("Selected X-axis is neither a valid DateTime nor numeric series for scientific plotting.")
            return

        plot_df = pd.DataFrame({"X": plot_x, "Y": y_num}).dropna()
        if len(plot_df) < 2:
            st.error("At least two valid X-Y observations are required.")
            return
        if x_type == "DateTime":
            plot_df = plot_df.sort_values("X")
            if plot_df["X"].duplicated().any():
                st.warning("Duplicate DateTime values exist; the chart will retain them but chronological ordering is applied.")

        st.success(f"✓ X-axis verified: {x_type} | Y-axis verified: numeric | Valid points: {len(plot_df)}")
        if chart_type == "Line":
            fig = px.line(plot_df, x="X", y="Y", markers=True, title=f"{y_col} vs {x_col}")
        elif chart_type == "Bar":
            fig = px.bar(plot_df, x="X", y="Y", title=f"{y_col} vs {x_col}")
        else:
            fig = px.scatter(plot_df, x="X", y="Y", title=f"{y_col} vs {x_col}")
        fig.update_layout(height=500, xaxis_title=str(x_col), yaxis_title=str(y_col), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(plot_df.rename(columns={"X": x_col, "Y": y_col}), use_container_width=True, hide_index=True)


# ============================================================
# PAGE ROUTER
# ============================================================

if st.session_state.page == "Dashboard":

    dashboard()

elif st.session_state.page == "🌧️ Hydrology":

    hydrology()

elif st.session_state.page == "☀️ Evapotranspiration":

    evapotranspiration()

elif st.session_state.page == "🇵🇰 Live Pakistan Water":

    live_pakistan_water()

elif st.session_state.page == "🌱 Crop & Climate":

    crop_climate()

elif st.session_state.page == "📊 Data Analysis":

    data_analysis()


elif st.session_state.page == "ℹ️ About This App":

    st.title("ℹ️ About HydroAgri Nexus")

    st.markdown("""
    <div class="glass-card" style="padding:32px; margin:10px 0 22px 0;">
        <div style="font-size:44px;">🌊</div>
        <h1 style="margin:6px 0 6px;">HydroAgri Nexus</h1>
        <p style="font-size:18px; opacity:0.85; margin:0;">
            Pakistan Hydrology & Agricultural Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 1])

    with col1:
        st.markdown("""
        <div class="glass-card" style="padding:26px; min-height:250px;">
            <h2>🌐 About This App</h2>
            <p style="line-height:1.8;">
                <b>HydroAgri Nexus</b> is an integrated hydro-agricultural
                intelligence platform designed to bring hydrology, climate,
                evapotranspiration, crop-water requirements, Pakistan water
                information, and data analysis together in one place.
            </p>
            <p style="line-height:1.8;">
                The application is designed to support scientific exploration
                and practical understanding of water resources by combining
                engineering calculations, analytical tools, visualizations,
                and hydro-climatic information.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="glass-card" style="padding:26px; min-height:250px;">
            <h2>👨‍💻 Developer</h2>
            <h2 style="margin:4px 0;">Junaid Burki</h2>
            <p style="font-size:18px; opacity:0.9; margin-top:0;">
                <b>Water Resource Engineer</b>
            </p>
            <p style="line-height:1.8;">
                HydroAgri Nexus is developed as a Pakistan-focused platform
                for water-resource analysis, agricultural water management,
                hydro-climatic understanding, and scientific decision support.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="padding:26px; margin-top:8px;">
        <h2>🧭 What HydroAgri Nexus Covers</h2>
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                    gap:15px; margin-top:18px;">
            <div class="mini-card">
                <b>🌧️ Hydrology</b><br>
                Rainfall, runoff, frequency analysis and hydrologic calculations.
            </div>
            <div class="mini-card">
                <b>☀️ Evapotranspiration</b><br>
                FAO-56 reference ET, crop ET and agricultural water demand.
            </div>
            <div class="mini-card">
                <b>🇵🇰 Pakistan Water</b><br>
                River and water information from relevant official sources.
            </div>
            <div class="mini-card">
                <b>🌱 Crop & Climate</b><br>
                Crop-water relationships and climate-related analysis.
            </div>
            <div class="mini-card">
                <b>📊 Data Analysis</b><br>
                Data upload, statistics, visualization and quality checks.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "HydroAgri Nexus | Live information sourced from official "
    "Pakistan hydrological and meteorological sources where available."
)