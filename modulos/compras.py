from datetime import date

import streamlit as st

from config.conexion import consultar, transaccion
from modulos.utilidades import (a_df, registrar_movimiento, sumar_inventario)


def mostrar_compras():
    st.header("Registrar compra")
    id_tienda = st.session_state["id_tienda"]

    proveedores = consultar("SELECT id_proveedor, nombre FROM proveedor WHERE id_tienda = %s ORDER BY nombre",
                            (id_tienda,))
    productos = consultar(
        """
        SELECT p.id_producto, p.nombre, p.requiere_vencimiento, u.abreviatura
        FROM producto p INNER JOIN unidad_medida u ON u.id_unidad = p.id_unidad
        ORDER BY p.nombre
        """
    )
    if not proveedores:
        st.warning("Primero registre al menos un proveedor.")
        return
    if not productos:
        st.warning("No hay productos en el catálogo.")
        return

    carrito = st.session_state.setdefault("carrito_compra", [])
    prov = st.selectbox("Proveedor", range(len(proveedores)), format_func=lambda i: proveedores[i]["nombre"])

    with st.form("form_linea_compra", clear_on_submit=True):
        idx = st.selectbox("Producto", range(len(productos)),
                           format_func=lambda i: f"{productos[i]['nombre']} ({productos[i]['abreviatura']})")
        cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0)
        precio_compra = st.number_input("Precio de compra por unidad ($)", min_value=0.0, value=0.0, step=0.05, format="%.2f")
        precio_venta = st.number_input("Precio de venta sugerido ($, opcional)", min_value=0.0, value=0.0, step=0.05, format="%.2f")
        vencimiento = st.date_input("Fecha de vencimiento (solo si el producto la requiere)", value=None)
        agregar = st.form_submit_button("Agregar a la compra")

    if agregar:
        p = productos[idx]
        if precio_compra <= 0:
            st.warning("El precio de compra debe ser mayor que cero.")
        elif p["requiere_vencimiento"] and vencimiento is None:
            st.warning("Este producto requiere fecha de vencimiento.")
        elif p["requiere_vencimiento"] and vencimiento < date.today():
            st.warning("La fecha de vencimiento no puede estar en el pasado.")
        else:
            carrito.append({
                "id_producto": p["id_producto"],
                "producto": p["nombre"],
                "cantidad": float(cantidad),
                "precio_compra": float(precio_compra),
                "precio_venta_sugerido": float(precio_venta) if precio_venta > 0 else None,
                "vencimiento": vencimiento if p["requiere_vencimiento"] else None,
            })

    total = 0.0
    if carrito:
        df = a_df(carrito)
        df["subtotal"] = df["cantidad"] * df["precio_compra"]
        total = round(float(df["subtotal"].sum()), 2)
        st.dataframe(df[["producto", "cantidad", "precio_compra", "vencimiento", "subtotal"]], hide_index=True)
        st.write(f"**Total: ${total:,.2f}**")

    col1, col2 = st.columns(2)
    if col1.button("Registrar compra", disabled=not carrito):
        try:
            with transaccion() as cur:
                cur.execute(
                    "INSERT INTO compra (id_tienda, id_proveedor, id_usuario, total) VALUES (%s, %s, %s, %s)",
                    (id_tienda, proveedores[prov]["id_proveedor"], st.session_state["id_usuario"], total),
                )
                id_compra = cur.lastrowid
                for item in carrito:
                    id_lote = None
                    if item["vencimiento"] is not None:
                        cur.execute(
                            "INSERT INTO lote (id_tienda, id_producto, fecha_vencimiento, cantidad_disponible) "
                            "VALUES (%s, %s, %s, %s)",
                            (id_tienda, item["id_producto"], item["vencimiento"], item["cantidad"]),
                        )
                        id_lote = cur.lastrowid
                    cur.execute(
                        "INSERT INTO detalle_compra (id_compra, id_producto, id_lote, cantidad, precio_compra, "
                        "precio_venta_sugerido) VALUES (%s, %s, %s, %s, %s, %s)",
                        (id_compra, item["id_producto"], id_lote, item["cantidad"], item["precio_compra"],
                         item["precio_venta_sugerido"]),
                    )
                    id_detalle = cur.lastrowid
                    sumar_inventario(cur, id_tienda, item["id_producto"], item["cantidad"],
                                     item["precio_venta_sugerido"])
                    registrar_movimiento(cur, id_tienda, item["id_producto"], id_lote, "COMPRA",
                                         item["cantidad"], id_detalle_compra=id_detalle)
                    cur.execute(
                        """
                        INSERT INTO producto_proveedor (id_producto, id_proveedor, ultimo_precio, fecha_ultima_compra)
                        VALUES (%s, %s, %s, CURDATE())
                        ON DUPLICATE KEY UPDATE ultimo_precio = VALUES(ultimo_precio),
                                                fecha_ultima_compra = VALUES(fecha_ultima_compra)
                        """,
                        (item["id_producto"], proveedores[prov]["id_proveedor"], item["precio_compra"]),
                    )
            st.session_state["carrito_compra"] = []
            st.success(f"Compra #{id_compra} registrada. El inventario fue actualizado.")
            st.rerun()
        except Exception as error:
            st.error(f"No se pudo registrar la compra: {error}")
    if col2.button("Vaciar compra"):
        st.session_state["carrito_compra"] = []
        st.rerun()
