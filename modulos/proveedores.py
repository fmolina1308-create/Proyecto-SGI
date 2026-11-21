import streamlit as st
import mysql.connector

from config.conexion import consultar, transaccion
from modulos.utilidades import a_df


def mostrar_proveedores():
    st.header("Proveedores")
    id_tienda = st.session_state["id_tienda"]

    with st.form("form_proveedor", clear_on_submit=True):
        nombre = st.text_input("Nombre del proveedor")
        dui_nit = st.text_input("DUI/NIT (opcional)")
        telefono = st.text_input("Teléfono")
        guardar = st.form_submit_button("Guardar proveedor")
    if guardar:
        if nombre.strip() == "":
            st.warning("Debe ingresar el nombre del proveedor.")
        else:
            try:
                with transaccion() as cur:
                    cur.execute(
                        "INSERT INTO proveedor (id_tienda, nombre, dui_nit, telefono) VALUES (%s, %s, %s, %s)",
                        (id_tienda, nombre.strip(), dui_nit.strip() or None, telefono.strip() or None),
                    )
                st.success("Proveedor registrado correctamente.")
            except mysql.connector.IntegrityError:
                st.error("Ya existe un proveedor con ese DUI/NIT.")
            except Exception as error:
                st.error(f"No se pudo registrar el proveedor: {error}")

    st.subheader("Proveedores de mi tienda")
    filas = consultar(
        "SELECT id_proveedor, nombre, dui_nit, telefono FROM proveedor WHERE id_tienda = %s ORDER BY nombre",
        (id_tienda,),
    )
    if filas:
        st.dataframe(a_df(filas), hide_index=True)
    else:
        st.info("Aún no hay proveedores registrados.")

    st.subheader("Productos que suministra cada proveedor")
    rel = consultar(
        """
        SELECT pr.nombre AS proveedor, p.nombre AS producto, pp.ultimo_precio, pp.fecha_ultima_compra
        FROM producto_proveedor pp
        INNER JOIN proveedor pr ON pr.id_proveedor = pp.id_proveedor
        INNER JOIN producto p ON p.id_producto = pp.id_producto
        WHERE pr.id_tienda = %s
        ORDER BY pr.nombre, p.nombre
        """,
        (id_tienda,),
    )
    if rel:
        st.dataframe(a_df(rel), hide_index=True)
    else:
        st.caption("La relación se llena automáticamente al registrar compras.")
