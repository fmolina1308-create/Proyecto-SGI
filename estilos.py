import streamlit as st

# Paleta suave (cámbiala aquí y se actualiza toda la app)
COLOR_PANEL = "linear-gradient(135deg, #E1E4E8 0%, #D6DBE0 55%, #CBD2D9 100%)"
COLOR_TITULO = "#1F2933"

# Cada botón del panel toma un color de esta lista, en orden
COLORES_BOTONES = [
    "#1F7A7A",  # turquesa (color principal del tema)
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
        .st-key-btn{i} button {{ background: {color}; }}
        """

    st.markdown(f"""
    <style>
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
            color: white;
            font-weight: 700;
            border: none;
            border-radius: 6px;
            width: 100%;
            min-height: 3rem;
        }}
        .st-key-panel .stButton > button:hover {{
            color: white;
            filter: brightness(1.12);
        }}
        {css_botones}
        .st-key-volver button {{
            background: {COLOR_VOLVER} !important;
            color: white !important;
            border: none !important;
            font-weight: 600;
        }}
        .st-key-volver button:hover {{
            background: {COLOR_VOLVER_HOVER} !important;
        }}
    </style>
    """, unsafe_allow_html=True)
