import streamlit as st

st.set_page_config(page_title="Sistema de tiendas y CD", layout="wide")

from modulos.administracion import mostrar_administracion
from modulos.compras import mostrar_compras
from modulos.envios import mostrar_envios
from modulos.inventario import mostrar_inventario
from modulos.login import login
from modulos.productos import mostrar_productos
from modulos.proveedores import mostrar_proveedores
from modulos.reportes import mostrar_reportes
from modulos.ventas import mostrar_ventas

CLAVES_SESION = ["sesion_iniciada", "usuario", "id_usuario", "nombre", "rol", "id_tienda", "tienda", "tipo_tienda"]

if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False


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


if st.session_state["sesion_iniciada"]:
    st.sidebar.title("Menú")
    st.sidebar.write(f"**{st.session_state['nombre']}**")
    st.sidebar.write(f"Rol: {st.session_state['rol']}")
    st.sidebar.write(f"Tienda: {st.session_state['tienda']}")
    opciones = menu_por_rol()
    seleccion = st.sidebar.selectbox("Seleccione una opción", list(opciones.keys()))
    opciones[seleccion]()

    if st.sidebar.button("Cerrar sesión"):
        for clave in list(st.session_state.keys()):
            del st.session_state[clave]
        st.rerun()
else:
    login()
