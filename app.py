import streamlit as st

st.set_page_config(page_title="Sistema de tiendas y CD", layout="wide")

from modulos.administracion import mostrar_administracion

from modulos.compras import mostrar_compras

from modulos.envios import mostrar_envios

from modulos.estilos import aplicar_estilos

from modulos.inventario import mostrar_inventario

from modulos.login import login

from modulos.productos import mostrar_productos

from modulos.proveedores import mostrar_proveedores

from modulos.reportes import mostrar_reportes

from modulos.ventas import mostrar_ventas

aplicar_estilos()

CLAVES_SESION = ["sesion_iniciada", "usuario", "id_usuario", "nombre", "rol", "id_tienda", "tienda", "tipo_tienda"]

ICONOS = {
    "Inventario": "📋",
    "Productos": "📦",
    "Proveedores": "🏪",
    "Compras": "🛒",
    "Ventas": "🤝",
    "Despachos a tiendas": "🚚",
    "Envíos del CD": "🚚",
    "Reportes": "📊",
    "Administración": "⚙️",
}

COLUMNAS_PANEL = 3

if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False

if "pagina" not in st.session_state:
    st.session_state["pagina"] = None


def ir_a(pagina):
    st.session_state["pagina"] = pagina


def menu_por_rol():
    """Devuelve {opcion: funcion} segun el rol y el tipo de tienda del usuario."""
    rol = st.session_state["rol"]
    es_cd = st.session_state["tipo_tienda"] == "CD"
    if rol == "Administrador":
        return {
            "Inventario": mostrar_inventario,
            "Productos": mostrar_productos,
            "Reportes": mostrar_reportes,
            "Administración": mostrar_administracion,
        }
    if rol == "Vendedor":
        return {"Ventas": mostrar_ventas, "Inventario": mostrar_inventario}
    menu = {
        "Inventario": mostrar_inventario,
        "Productos": mostrar_productos,
        "Proveedores": mostrar_proveedores,
        "Compras": mostrar_compras,
        "Ventas": mostrar_ventas,
        "Despachos a tiendas" if es_cd else "Envíos del CD": mostrar_envios,
        "Reportes": mostrar_reportes,
    }
    return menu


def panel_principal(opciones):
    with st.container(key="panel"):
        st.markdown('<div class="panel-titulo">PANEL PRINCIPAL</div>', unsafe_allow_html=True)
        nombres = list(opciones.keys())
        for i in range(0, len(nombres), COLUMNAS_PANEL):
            cols = st.columns(COLUMNAS_PANEL)
            for j, (col, nombre) in enumerate(zip(cols, nombres[i:i + COLUMNAS_PANEL])):
                with col:
                    st.markdown(f'<div class="icono">{ICONOS.get(nombre, "🧩")}</div>', unsafe_allow_html=True)
                    with st.container(key=f"btn{i + j}"):
                        st.button(nombre, key=f"menu_{nombre}", on_click=ir_a, args=(nombre,))
        st.write("")


if st.session_state["sesion_iniciada"]:
    st.sidebar.title("Menú")
    st.sidebar.write(f"**{st.session_state['nombre']}**")
    st.sidebar.write(f"Rol: {st.session_state['rol']}")
    st.sidebar.write(f"Tienda: {st.session_state['tienda']}")

    opciones = menu_por_rol()

    if st.sidebar.button("Cerrar sesión"):
        for clave in list(st.session_state.keys()):
            del st.session_state[clave]
        st.rerun()

    pagina = st.session_state["pagina"]
    if pagina not in opciones:
        pagina = None

    if pagina is None:
        panel_principal(opciones)
    else:
        with st.container(key="volver"):
            st.button("⬅ Regresar al panel principal", on_click=ir_a, args=(None,))
        opciones[pagina]()
else:
    login()
