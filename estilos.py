import streamlit as st

# Paleta: gris piedra y turquesa (cámbiala aquí y se actualiza toda la app)
COLOR_PANEL = "linear-gradient(135deg, #E1E4E8 0%, #D6DBE0 55%, #CBD2D9 100%)"
COLOR_TITULO = "#1F2933"

# Color de TODOS los botones de la app (formularios, sidebar, módulos)
COLOR_BASE = "#1F7A7A"
COLOR_BASE_HOVER = "#2A8C8C"

# Los botones del panel principal toman un color de esta lista, en orden
COLORES_BOTONES = [
    "#1F7A7A",  # turquesa
    "#3E4C59",  # gris pizarra oscuro
    "#17605F",  # turquesa profundo
    "#52606D",  # gris azulado
    "#2A8C8C",  # turquesa medio
    "#616E7C",  # gris piedra
]

COLOR_VOLVER = "#1F2933"
COLOR_VOLVER_HOVER = "#323F4B"
MAX_BOTONES = 24


def aplicar_estilos():
    css_botones = ""
    for i in range(MAX_BOTONES):
        color = COLORES_BOTONES[i % len(COLORES_BOTONES)]
        css_botones += f"""
        .st-key-panel .st-key-btn{i} .stButton > button {{ background: {color}; }}
        """

    st.markdown(f"""
    <style>
        /* ---- Todos los botones de la app ---- */
        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {{
            background: {COLOR_BASE};
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 6px;
        }}
        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {{
            background: {COLOR_BASE_HOVER};
            color: white;
        }}
        .stButton > button:focus,
        .stFormSubmitButton > button:focus {{
            color: white;
            box-shadow: none;
        }}

        /* ---- Panel principal ---- */
        .st-key-panel {{
            background: {COLOR_PANEL};
            border-radius: 14px;
            padding: 1.5rem 1.5rem 1rem 1.5rem;
        }}
        .panel-titulo {{
            color: {COLOR_TITULO};
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0 0 1rem 0;
        }}
        .icono {{
            text-align: center;
            font-size: 3.2rem;
            line-height: 1.2;
            margin-top: 0.8rem;
        }}
        .st-key-panel .stButton > button {{
            width: 100%;
            min-height: 3rem;
            font-weight: 700;
        }}
        .st-key-panel .stButton > button:hover {{
            filter: brightness(1.12);
        }}
        {css_botones}

        /* ---- Botón de regreso ---- */
        .st-key-volver .stButton > button {{
            background: {COLOR_VOLVER};
        }}
        .st-key-volver .stButton > button:hover {{
            background: {COLOR_VOLVER_HOVER};
        }}
    </style>
    """, unsafe_allow_html=True)
