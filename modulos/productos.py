import streamlit as st
import mysql.connector

from config.conexion import consultar, transaccion
from modulos.utilidades import a_df


def mostrar_productos():
    st.header("Productos")
    id_tienda = st.session_state["id_tienda"]
    es_cd = st.session_state["tipo_tienda"] == "CD"
    es_admin = st.session_state["rol"] == "Administrador"

    tab_lista, tab_nuevo, tab_config = st.tabs(
        ["Catálogo", "Nuevo producto", "Precio y stock mínimo de mi tienda"]
    )

    categorias = consultar("SELECT id_categoria, nombre FROM categoria ORDER BY nombre")
    unidades = consultar("SELECT id_unidad, nombre, abreviatura FROM unidad_medida ORDER BY nombre")
    productos = consultar(
        """
        SELECT p.id_producto, p.nombre, c.nombre AS categoria, u.abreviatura AS unidad,
               p.requiere_vencimiento
        FROM producto p
        INNER JOIN categoria c ON c.id_categoria = p.id_categoria
        INNER JOIN unidad_medida u ON u.id_unidad = p.id_unidad
        ORDER BY p.nombre
        """
    )

    with tab_lista:
        if productos:
            df = a_df(productos)
            df["requiere_vencimiento"] = df["requiere_vencimiento"].map(lambda v: "Sí" if v else "No")
            st.dataframe(df, hide_index=True)
        else:
            st.info("Todavía no hay productos registrados.")

    with tab_nuevo:
        if es_cd and not es_admin:
            st.info("El Centro de Distribución opera con el catálogo existente y no puede registrar productos nuevos.")
        elif not categorias or not unidades:
            st.warning("Primero debe existir al menos una categoría y una unidad de medida (módulo Administración).")
        else:
            with st.form("form_producto", clear_on_submit=True):
                nombre = st.text_input("Nombre del producto")
                cat = st.selectbox("Categoría", range(len(categorias)), format_func=lambda i: categorias[i]["nombre"])
                uni = st.selectbox("Unidad de medida", range(len(unidades)),
                                   format_func=lambda i: f"{unidades[i]['nombre']} ({unidades[i]['abreviatura']})")
                venc = st.checkbox("Requiere fecha de vencimiento")
                guardar = st.form_submit_button("Guardar producto")
            if guardar:
                if nombre.strip() == "":
                    st.warning("Debe ingresar el nombre del producto.")
                else:
                    existe = consultar("SELECT id_producto FROM producto WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
                                       (nombre.strip(),))
                    if existe:
                        st.warning("Ya existe un producto con ese nombre.")
                    else:
                        try:
                            with transaccion() as cur:
                                cur.execute(
                                    "INSERT INTO producto (nombre, id_categoria, id_unidad, requiere_vencimiento) "
                                    "VALUES (%s, %s, %s, %s)",
                                    (nombre.strip(), categorias[cat]["id_categoria"], unidades[uni]["id_unidad"], venc),
                                )
                                id_p = cur.lastrowid
                                cur.execute(
                                    "INSERT INTO inventario (id_tienda, id_producto, existencia) VALUES (%s, %s, 0)",
                                    (id_tienda, id_p),
                                )
                            st.success("Producto registrado y agregado al inventario de su tienda.")
                        except Exception as error:
                            st.error(f"No se pudo registrar el producto: {error}")

    with tab_config:
        if not productos:
            st.info("No hay productos para configurar.")
        else:
            with st.form("form_config_inv"):
                idx = st.selectbox("Producto", range(len(productos)), format_func=lambda i: productos[i]["nombre"])
                precio = st.number_input("Precio de venta ($)", min_value=0.0, value=0.0, step=0.05, format="%.2f")
                minimo = st.number_input("Stock mínimo", min_value=0.0, value=0.0, step=1.0)
                guardar = st.form_submit_button("Guardar configuración")
            if guardar:
                if precio <= 0:
                    st.warning("El precio de venta debe ser mayor que cero.")
                else:
                    try:
                        with transaccion() as cur:
                            cur.execute(
                                """
                                INSERT INTO inventario (id_tienda, id_producto, existencia, stock_minimo, precio_venta)
                                VALUES (%s, %s, 0, %s, %s)
                                ON DUPLICATE KEY UPDATE stock_minimo = VALUES(stock_minimo),
                                                        precio_venta = VALUES(precio_venta)
                                """,
                                (id_tienda, productos[idx]["id_producto"], minimo, precio),
                            )
                        st.success("Configuración guardada.")
                    except Exception as error:
                        st.error(f"No se pudo guardar: {error}")
