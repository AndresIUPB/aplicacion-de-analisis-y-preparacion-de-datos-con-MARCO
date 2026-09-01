"""
Dashboard Streamlit para la estación 31 de CORNARE / MARCO.

Estación: Quebrada La Bolsa · Marinilla · Red Agua

Ejecución:
    streamlit run app_nivel_cornare.py
"""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Identidad fija de la aplicación.
CODIGO_ESTACION = "31"
NOMBRE_ESTACION = "Quebrada La Bolsa"
MUNICIPIO = "Marinilla"
DEPARTAMENTO = "Antioquia"
RED = "Agua"

# El código original usa este punto solo cuando la API no informa coordenadas.
# Nunca se presenta como la ubicación real de la estación.
LAT_DEFECTO = 6.2766
LON_DEFECTO = -75.5901

API_BASE_URL = "https://marco.cornare.gov.co/api/v1/estaciones"
LLAVE_FECHA = "level_date"
LLAVE_VALOR = "level"
CANDIDATOS_LAT = ["lat", "latitude", "latitud"]
CANDIDATOS_LON = ["lng", "lon", "longitude", "longitud"]

st.set_page_config(
    page_title="La Bolsa · Monitoreo hidrológico",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Estilos
# -----------------------------------------------------------------------------
def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #102a33;
            --muted: #667d84;
            --ocean: #0b6e75;
            --aqua: #2b9ba2;
            --mint: #dff3ef;
            --line: rgba(29, 88, 96, .12);
            --surface: rgba(255, 255, 255, .78);
        }

        .stApp {
            color: var(--ink);
            background:
                radial-gradient(circle at 8% 0%, rgba(98, 196, 190, .17), transparent 30rem),
                radial-gradient(circle at 96% 4%, rgba(66, 141, 174, .13), transparent 32rem),
                linear-gradient(180deg, #f4faf9 0%, #edf6f5 52%, #f7faf9 100%);
        }
        [data-testid="stHeader"] { background: rgba(244, 250, 249, .68); }
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1440px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }
        [data-testid="stSidebar"] {
            background: rgba(245, 251, 250, .92);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] .block-container { padding-top: 2rem; }

        h1, h2, h3, p { letter-spacing: -.02em; }
        h2 { color: var(--ink); font-size: 1.45rem !important; }

        .hero {
            position: relative;
            overflow: hidden;
            padding: clamp(1.5rem, 4vw, 3.2rem);
            margin-bottom: 1.4rem;
            border: 1px solid rgba(255,255,255,.82);
            border-radius: 30px;
            background: linear-gradient(125deg, rgba(7, 69, 80, .96), rgba(12, 111, 117, .91) 58%, rgba(54, 150, 151, .84));
            box-shadow: 0 24px 70px rgba(18, 75, 82, .16);
            color: white;
        }
        .hero::after {
            content: "";
            position: absolute;
            width: 24rem;
            height: 24rem;
            right: -8rem;
            top: -13rem;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,.22);
            box-shadow: 0 0 0 3.5rem rgba(255,255,255,.035), 0 0 0 7rem rgba(255,255,255,.025);
        }
        .hero-kicker { font-size: .76rem; font-weight: 700; letter-spacing: .14em; opacity: .78; }
        .hero h1 { margin: .7rem 0 .3rem; color: white; font-size: clamp(2.15rem, 5vw, 4.4rem); line-height: 1; }
        .hero-sub { margin: 0; font-size: clamp(1rem, 2vw, 1.24rem); opacity: .82; }
        .badge-row { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.5rem; }
        .badge {
            padding: .42rem .72rem;
            border: 1px solid rgba(255,255,255,.22);
            border-radius: 999px;
            background: rgba(255,255,255,.1);
            backdrop-filter: blur(12px);
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .07em;
        }

        .section-label {
            margin: 1.8rem 0 .28rem;
            color: var(--ocean);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .section-title { margin: 0 0 .35rem; font-size: clamp(1.35rem, 2.5vw, 1.8rem); font-weight: 720; }
        .section-copy { margin: 0 0 1.1rem; color: var(--muted); font-size: .93rem; }

        .metric-card, .glass-card, [data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,.9);
            background: var(--surface);
            box-shadow: 0 12px 35px rgba(40, 82, 87, .075);
            backdrop-filter: blur(16px);
        }
        .metric-card {
            min-height: 138px;
            padding: 1.15rem 1.2rem;
            border-radius: 22px;
            margin-bottom: .65rem;
        }
        .metric-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 10px;
            background: var(--mint);
            color: var(--ocean);
            font-size: .9rem;
            font-weight: 800;
        }
        .metric-label { margin-top: .8rem; color: var(--muted); font-size: .78rem; font-weight: 650; }
        .metric-value { margin-top: .12rem; color: var(--ink); font-size: clamp(1.55rem, 3vw, 2.2rem); font-weight: 760; line-height: 1.08; }
        .metric-note { margin-top: .3rem; color: #789096; font-size: .7rem; }

        .glass-card { padding: 1.2rem 1.3rem; border-radius: 22px; }
        .status-line { display: flex; align-items: center; gap: .5rem; font-size: .78rem; font-weight: 750; color: var(--ocean); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #2d9d78; box-shadow: 0 0 0 5px rgba(45,157,120,.10); }
        .muted { color: var(--muted); }
        .tiny { font-size: .76rem; }
        .quality-score { font-size: 2.3rem; font-weight: 780; color: var(--ink); line-height: 1; }
        .quality-score span { font-size: .85rem; color: var(--muted); font-weight: 600; }
        .progress-track { height: 10px; margin: .8rem 0 .55rem; overflow: hidden; border-radius: 99px; background: #dfecea; }
        .progress-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #167d82, #63bbb0); }
        .quality-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; margin-top: 1rem; }
        .quality-item { padding: .8rem; border-radius: 14px; background: rgba(228,243,240,.62); }
        .quality-item b { display: block; font-size: 1.05rem; color: var(--ink); }
        .quality-item span { color: var(--muted); font-size: .7rem; }

        div[data-testid="stPlotlyChart"] {
            overflow: hidden;
            border: 1px solid rgba(255,255,255,.88);
            border-radius: 24px;
            background: rgba(255,255,255,.74);
            box-shadow: 0 12px 35px rgba(40,82,87,.07);
        }
        [data-testid="stDataFrame"] { overflow: hidden; border-radius: 18px; }
        [data-testid="stDownloadButton"] button, [data-testid="stSidebar"] .stButton button {
            min-height: 3rem;
            border: 0;
            border-radius: 14px;
            background: linear-gradient(135deg, #0b6e75, #258f94);
            color: white;
            font-weight: 700;
            box-shadow: 0 10px 24px rgba(11,110,117,.18);
        }
        [data-testid="stDownloadButton"] button:hover, [data-testid="stSidebar"] .stButton button:hover {
            color: white;
            filter: brightness(1.04);
            transform: translateY(-1px);
        }
        [data-baseweb="tab-list"] { gap: .35rem; }
        [data-baseweb="tab"] { border-radius: 12px; padding: .65rem 1rem; }

        @media (max-width: 700px) {
            [data-testid="stAppViewContainer"] > .main .block-container { padding: 1rem .9rem 3rem; }
            .hero { border-radius: 24px; padding: 1.5rem; }
            .metric-card { min-height: 122px; }
            .quality-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def encabezado_seccion(etiqueta: str, titulo: str, descripcion: str = "") -> None:
    st.markdown(
        f'<div class="section-label">{etiqueta}</div>'
        f'<div class="section-title">{titulo}</div>'
        f'<div class="section-copy">{descripcion}</div>',
        unsafe_allow_html=True,
    )


def tarjeta_metrica(icono: str, etiqueta: str, valor: str, nota: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icono}</div>
            <div class="metric-label">{etiqueta}</div>
            <div class="metric-value">{valor}</div>
            <div class="metric-note">{nota}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Consulta y preparación de datos
# -----------------------------------------------------------------------------
def _headers_api() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }


@st.cache_data(ttl=300, show_spinner=False)
def obtener_serie_nivel(
    codigo_estacion: str,
    desde: str,
    hasta: str,
    calidad: int = 1,
    timeout: int = 30,
) -> tuple[dict[str, Any] | None, str | None]:
    """Consulta la primera página de la serie sin modificar el contrato original."""
    url = f"{API_BASE_URL}/{codigo_estacion}/nivel"
    params = {"desde": desde, "hasta": hasta, "calidad": calidad}
    try:
        respuesta = requests.get(
            url,
            params=params,
            headers=_headers_api(),
            timeout=timeout,
            verify=False,
        )
        if respuesta.status_code == 200:
            return respuesta.json(), None
        return None, f"HTTP {respuesta.status_code}"
    except requests.exceptions.JSONDecodeError:
        return None, "La API respondió, pero el contenido no tiene formato JSON válido."
    except requests.exceptions.RequestException as exc:
        return None, f"Error de red: {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def obtener_todas_las_paginas(datos_json: dict[str, Any], timeout: int = 30) -> list[dict[str, Any]]:
    """Recorre la paginación `next` y conserva todos los registros disponibles."""
    registros = list(datos_json.get("values", []))
    siguiente_url = datos_json.get("next")

    while siguiente_url:
        try:
            respuesta = requests.get(
                siguiente_url,
                headers=_headers_api(),
                timeout=timeout,
                verify=False,
            )
            if respuesta.status_code != 200:
                break
            pagina = respuesta.json()
        except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError):
            break

        registros.extend(pagina.get("values", []))
        siguiente_url = pagina.get("next")

    return registros


def detectar_coordenadas(datos_json: Any) -> tuple[float, float, bool]:
    """Busca un par lat/lon real en la respuesta; si no existe, devuelve el respaldo original."""
    pendientes = [datos_json]
    while pendientes:
        elemento = pendientes.pop(0)
        if isinstance(elemento, dict):
            lat = next((elemento[k] for k in CANDIDATOS_LAT if k in elemento), None)
            lon = next((elemento[k] for k in CANDIDATOS_LON if k in elemento), None)
            if lat is not None and lon is not None:
                try:
                    return float(lat), float(lon), True
                except (TypeError, ValueError):
                    pass
            pendientes.extend(elemento.values())
        elif isinstance(elemento, list):
            pendientes.extend(elemento)
    return LAT_DEFECTO, LON_DEFECTO, False


def preparar_dataframe(registros: list[dict[str, Any]]) -> pd.DataFrame:
    """Normaliza las dos llaves conocidas y conserva las demás columnas de la API."""
    df = pd.DataFrame(registros).rename(columns={LLAVE_FECHA: "fecha", LLAVE_VALOR: "nivel"})
    if "fecha" not in df.columns or "nivel" not in df.columns:
        return pd.DataFrame()

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["nivel"] = pd.to_numeric(df["nivel"], errors="coerce")
    return df.dropna(subset=["fecha", "nivel"]).sort_values("fecha").reset_index(drop=True)


def mascara_outliers(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=bool)
    q1, q3 = df["nivel"].quantile(0.25), df["nivel"].quantile(0.75)
    iqr = q3 - q1
    limite_inferior, limite_superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (df["nivel"] < limite_inferior) | (df["nivel"] > limite_superior) | (df["nivel"] < 0)


def calcular_indice_calidad(df: pd.DataFrame) -> tuple[float, int, int, float]:
    """Índice original: completitud (70 %) + proporción sin outliers (30 %)."""
    if df.empty or len(df) < 2:
        return 0.0, 0, 0, 0.0

    fechas_unicas = df.drop_duplicates(subset="fecha").set_index("fecha")
    frecuencia_tipica = df["fecha"].diff().dropna().mode()
    if frecuencia_tipica.empty or frecuencia_tipica.iloc[0] <= pd.Timedelta(0):
        return 0.0, 0, int(mascara_outliers(df).sum()), 0.0

    rango_completo = pd.date_range(
        start=fechas_unicas.index.min(),
        end=fechas_unicas.index.max(),
        freq=frecuencia_tipica.iloc[0],
    )
    esperados = len(rango_completo)
    huecos = max(0, esperados - len(fechas_unicas))
    completitud = max(0.0, min(1.0, 1 - (huecos / esperados))) if esperados else 0.0

    outliers = mascara_outliers(df)
    proporcion_outliers = float(outliers.mean())
    indice = (completitud * 0.7 + (1 - proporcion_outliers) * 0.3) * 100
    return round(indice, 1), huecos, int(outliers.sum()), round(completitud * 100, 1)


# -----------------------------------------------------------------------------
# Gráficos
# -----------------------------------------------------------------------------
def estilo_figura(figura: go.Figure, altura: int = 430) -> go.Figure:
    figura.update_layout(
        height=altura,
        margin=dict(l=28, r=24, t=28, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Arial, sans-serif", color="#3d5c63", size=12),
        hoverlabel=dict(bgcolor="#103f48", font_color="white", bordercolor="#103f48"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        modebar=dict(bgcolor="rgba(255,255,255,.7)"),
    )
    figura.update_xaxes(showgrid=False, zeroline=False, title=None)
    figura.update_yaxes(gridcolor="rgba(31,92,99,.10)", zeroline=False, title="Nivel reportado")
    return figura


def grafico_serie(df: pd.DataFrame) -> go.Figure:
    promedio = df["nivel"].mean()
    indice_maximo = df["nivel"].idxmax()
    indice_minimo = df["nivel"].idxmin()

    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["nivel"],
            name="Nivel",
            mode="lines",
            line=dict(color="#117f87", width=2.6, shape="spline", smoothing=0.45),
            fill="tozeroy",
            fillcolor="rgba(62, 166, 165, .10)",
            hovertemplate="%{x|%d %b %Y · %H:%M}<br><b>%{y:.3f}</b><extra></extra>",
        )
    )
    figura.add_hline(
        y=promedio,
        line_width=1.3,
        line_dash="dot",
        line_color="#80999e",
        annotation_text=f"Promedio {promedio:.2f}",
        annotation_position="top right",
        annotation_font_color="#667d84",
    )
    extremos = df.loc[[indice_maximo, indice_minimo]]
    figura.add_trace(
        go.Scatter(
            x=extremos["fecha"],
            y=extremos["nivel"],
            name="Extremos",
            mode="markers",
            marker=dict(size=10, color=["#e29b62", "#55a99c"], line=dict(color="white", width=2)),
            hovertemplate="%{x|%d %b %Y · %H:%M}<br><b>%{y:.3f}</b><extra></extra>",
        )
    )
    figura.update_layout(hovermode="x unified")
    figura.update_xaxes(rangeslider_visible=False)
    return estilo_figura(figura)


def grafico_distribucion(df: pd.DataFrame) -> go.Figure:
    bins = max(5, min(30, int(np.sqrt(len(df)))))
    figura = go.Figure(
        go.Histogram(
            x=df["nivel"],
            nbinsx=bins,
            marker_color="#31969a",
            opacity=.84,
            hovertemplate="Nivel: %{x}<br>Lecturas: %{y}<extra></extra>",
        )
    )
    figura.update_xaxes(title="Nivel reportado", showgrid=False)
    figura.update_yaxes(title="Número de lecturas")
    return estilo_figura(figura, 350)


def grafico_variacion(df: pd.DataFrame) -> go.Figure:
    variacion = df["nivel"].diff()
    colores = np.where(variacion >= 0, "#2a918c", "#d17d68")
    figura = go.Figure(
        go.Bar(
            x=df["fecha"],
            y=variacion,
            marker_color=colores,
            hovertemplate="%{x|%d %b · %H:%M}<br>Variación: %{y:.3f}<extra></extra>",
        )
    )
    figura.add_hline(y=0, line_width=1, line_color="rgba(43,77,82,.35)")
    figura.update_yaxes(title="Cambio entre lecturas")
    return estilo_figura(figura, 350)


# -----------------------------------------------------------------------------
# Interfaz
# -----------------------------------------------------------------------------
aplicar_estilos()

with st.sidebar:
    st.markdown("### Panel de consulta")
    st.caption("Ajusta el periodo y actualiza los registros de la estación.")
    st.text_input("Estación seleccionada", value="31 · Quebrada La Bolsa", disabled=True)

    fecha_desde_obj = st.date_input("Fecha inicial", value=date(2026, 8, 23))
    fecha_hasta_obj = st.date_input("Fecha final", value=date(2026, 8, 30))
    opcion_calidad = st.selectbox(
        "Calidad de datos",
        options=["Solo datos validados", "Todos los datos disponibles"],
        index=0,
        help="La opción validada envía calidad=1 a la API; la segunda envía calidad=0.",
    )
    calidad = 1 if opcion_calidad == "Solo datos validados" else 0
    consultar = st.button("Actualizar consulta", type="primary", width="stretch")

    st.markdown("---")
    st.caption("FUENTE DE DATOS")
    st.markdown("**CORNARE / MARCO**")
    st.caption("Red Agua · Código 31")

st.markdown(
    f"""
    <section class="hero">
        <div class="hero-kicker">MONITOREO HIDROLÓGICO</div>
        <h1>La Bolsa</h1>
        <p class="hero-sub">{MUNICIPIO} · {DEPARTAMENTO}</p>
        <div class="badge-row">
            <span class="badge">RED {RED.upper()}</span>
            <span class="badge">ESTACIÓN {CODIGO_ESTACION}</span>
            <span class="badge">FUENTE CORNARE / MARCO</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

if fecha_desde_obj > fecha_hasta_obj:
    st.error("La fecha inicial debe ser anterior o igual a la fecha final.")
    st.stop()

# Primera carga automática; después, los resultados se actualizan con el botón.
if "resultado_estacion_31" not in st.session_state:
    consultar = True

if consultar:
    with st.spinner("Estamos consultando los registros de la estación…"):
        datos_crudos, error = obtener_serie_nivel(
            CODIGO_ESTACION,
            fecha_desde_obj.strftime("%Y-%m-%d"),
            fecha_hasta_obj.strftime("%Y-%m-%d"),
            calidad,
        )

        if error:
            st.session_state.resultado_estacion_31 = {"estado": "error", "detalle": error}
        else:
            registros = obtener_todas_las_paginas(datos_crudos or {})
            df_consulta = preparar_dataframe(registros)
            if df_consulta.empty:
                st.session_state.resultado_estacion_31 = {"estado": "vacio"}
            else:
                lat, lon, coords_reales = detectar_coordenadas(datos_crudos)
                st.session_state.resultado_estacion_31 = {
                    "estado": "ok",
                    "df": df_consulta,
                    "lat": lat,
                    "lon": lon,
                    "coords_reales": coords_reales,
                    "desde": fecha_desde_obj.strftime("%Y-%m-%d"),
                    "hasta": fecha_hasta_obj.strftime("%Y-%m-%d"),
                    "calidad": calidad,
                }

resultado = st.session_state.get("resultado_estacion_31", {"estado": "vacio"})

if resultado["estado"] == "error":
    st.error("No fue posible obtener los registros en este momento. Intenta nuevamente en unos minutos.")
    with st.expander("Detalle técnico"):
        st.code(resultado.get("detalle", "Error no especificado"))
    st.stop()

if resultado["estado"] == "vacio":
    st.warning("No se encontraron registros para la estación 31 en el periodo seleccionado.")
    st.caption("Prueba ampliando el rango de fechas o consultando todos los datos disponibles.")
    st.stop()

df = resultado["df"]
indice_calidad, huecos, n_outliers, completitud = calcular_indice_calidad(df)
ultimo = df.iloc[-1]
fecha_ultima = ultimo["fecha"].strftime("%d %b %Y · %H:%M")

encabezado_seccion(
    "Resumen del periodo",
    "Lectura rápida",
    f"Registros consultados desde {resultado['desde']} hasta {resultado['hasta']}.",
)

metricas = st.columns(4)
with metricas[0]:
    tarjeta_metrica("↗", "Nivel más reciente", f"{ultimo['nivel']:.2f}", fecha_ultima)
with metricas[1]:
    tarjeta_metrica("≈", "Nivel promedio", f"{df['nivel'].mean():.2f}", "Promedio del periodo")
with metricas[2]:
    tarjeta_metrica("↑", "Máximo registrado", f"{df['nivel'].max():.2f}", "Valor máximo del periodo")
with metricas[3]:
    tarjeta_metrica("↓", "Mínimo registrado", f"{df['nivel'].min():.2f}", "Valor mínimo del periodo")

encabezado_seccion(
    "Serie temporal",
    "Evolución del nivel",
    "Explora la serie con el cursor; utiliza las herramientas del gráfico para ampliar o desplazarte.",
)
st.plotly_chart(grafico_serie(df), width="stretch", config={"displaylogo": False, "scrollZoom": True})

encabezado_seccion(
    "Análisis",
    "Patrones del periodo",
    "Visualizaciones complementarias para entender la distribución y los cambios entre lecturas.",
)
tab_distribucion, tab_variacion = st.tabs(["Distribución", "Variación entre lecturas"])
with tab_distribucion:
    st.plotly_chart(grafico_distribucion(df), width="stretch", config={"displaylogo": False})
    st.caption("Agrupa las lecturas por rangos para mostrar en qué niveles se concentran los datos.")
with tab_variacion:
    if len(df) >= 2:
        st.plotly_chart(grafico_variacion(df), width="stretch", config={"displaylogo": False})
        st.caption("Cada barra representa el cambio frente a la lectura inmediatamente anterior.")
    else:
        st.info("Se necesitan al menos dos lecturas para calcular variaciones.")

encabezado_seccion(
    "Calidad",
    "Estado de los datos consultados",
    "El índice resume completitud y presencia de valores atípicos; no representa el estado operativo de la estación.",
)
calidad_col, estado_col = st.columns([1.45, 1])
with calidad_col:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="status-line"><span class="status-dot"></span> DATOS DISPONIBLES</div>
            <div style="height:.9rem"></div>
            <div class="quality-score">{indice_calidad:.1f} <span>/ 100</span></div>
            <div class="progress-track"><div class="progress-fill" style="width:{max(0, min(100, indice_calidad))}%"></div></div>
            <div class="muted tiny">70 % completitud de la serie + 30 % proporción de datos sin outliers.</div>
            <div class="quality-grid">
                <div class="quality-item"><b>{len(df):,}</b><span>Lecturas válidas</span></div>
                <div class="quality-item"><b>{huecos:,}</b><span>Huecos estimados</span></div>
                <div class="quality-item"><b>{n_outliers:,}</b><span>Outliers detectados</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with estado_col:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="metric-label">COMPLETITUD ESTIMADA</div>
            <div class="metric-value">{completitud:.1f}%</div>
            <p class="muted tiny">Se estima a partir de la frecuencia temporal más común en el periodo consultado.</p>
            <div class="metric-label">FILTRO DE API</div>
            <div style="font-weight:700;margin-top:.25rem">{'Solo datos validados' if resultado['calidad'] == 1 else 'Todos los datos disponibles'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

encabezado_seccion(
    "Ubicación",
    "Ubicación de la estación",
    f"{NOMBRE_ESTACION} · {MUNICIPIO}",
)
mapa_col, ficha_col = st.columns([1.65, 1])
with mapa_col:
    if resultado["coords_reales"]:
        st.map(pd.DataFrame({"lat": [resultado["lat"]], "lon": [resultado["lon"]]}), zoom=12)
    else:
        st.info("La respuesta de la API no incluyó coordenadas verificables para esta consulta.")
        st.caption("No se muestra el punto de respaldo como si fuera la ubicación real de la estación.")
with ficha_col:
    estado_coord = "Entregadas por la API" if resultado["coords_reales"] else "No disponibles en la respuesta"
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="metric-label">ESTACIÓN</div><div style="font-weight:750;font-size:1.15rem">31 · La Bolsa</div>
            <div style="height:.9rem"></div>
            <div class="metric-label">MUNICIPIO</div><div style="font-weight:650">Marinilla · Antioquia</div>
            <div style="height:.9rem"></div>
            <div class="metric-label">RED</div><div style="font-weight:650">Agua</div>
            <div style="height:.9rem"></div>
            <div class="metric-label">COORDENADAS</div><div class="muted tiny">{estado_coord}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

encabezado_seccion(
    "Datos",
    "Registros consultados",
    "Consulta la información normalizada; las columnas adicionales de la API se conservan cuando están disponibles.",
)
columnas_ordenadas = ["fecha", "nivel"] + [c for c in df.columns if c not in {"fecha", "nivel"}]
st.dataframe(
    df[columnas_ordenadas],
    width="stretch",
    hide_index=True,
    column_config={
        "fecha": st.column_config.DatetimeColumn("Fecha y hora", format="DD/MM/YYYY HH:mm:ss"),
        "nivel": st.column_config.NumberColumn("Nivel reportado", format="%.3f"),
    },
)

encabezado_seccion(
    "Exportación",
    "Descargar datos",
    "Guarda los registros del periodo consultado para analizarlos posteriormente.",
)
csv = df[columnas_ordenadas].to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Descargar CSV",
    data=csv,
    file_name="nivel_quebrada_la_bolsa_estacion_31.csv",
    mime="text/csv",
    width="content",
)

encabezado_seccion("Contexto", "Sobre esta estación")
st.markdown(
    """
    <div class="glass-card muted">
        Esta aplicación consulta y visualiza los registros de nivel asociados a la estación 31 de la
        Quebrada La Bolsa, en Marinilla, usando información proporcionada por CORNARE / MARCO.
        Los resultados, la calidad y las visualizaciones corresponden únicamente al periodo seleccionado.
    </div>
    """,
    unsafe_allow_html=True,
)
