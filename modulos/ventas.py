import streamlit as st

from config.conexion import consultar, transaccion
from modulos.utilidades import (consumir_lotes, registrar_movimiento, restar_inventario, ui_carrito)


def productos_disponibles(id_tienda):
    return consultar(
        """
        SELECT p.id_producto, p.nombre, u.abreviatura, i.existencia, i.precio_venta
        FROM inventario i
        INNER JOIN producto p ON p.id_producto = i.id_producto
        INNER JOIN unidad_medida u ON u.id_unidad = p.id_unidad
        WHERE i.id_tienda = %s AND i.existencia > 0 AND i.precio_venta IS NOT NULL
        ORDER BY p.nombre
        """,
        (id_tienda,),
    )


def mostrar_ventas():
    st.header("Registrar venta")
    id_tienda = st.session_state["id_tienda"]
    productos = productos_disponibles(id_tienda)
    if not productos:
        st.info("No hay productos con existencia y precio de venta definido en esta tienda.")
        return

    carrito, total = ui_carrito("carrito_venta", productos)

    col1, col2 = st.columns(2)
    if col1.button("Registrar venta", disabled=not carrito):
        try:
            with transaccion() as cur:
                cur.execute(
                    "INSERT INTO venta (id_tienda, id_usuario, tipo_venta, total) VALUES (%s, %s, 'VENTA_CLIENTE', %s)",
                    (id_tienda, st.session_state["id_usuario"], total),
                )
                id_venta = cur.lastrowid
                for item in carrito:
                    restar_inventario(cur, id_tienda, item["id_producto"], item["cantidad"])
                    for id_lote, cant in consumir_lotes(cur, id_tienda, item["id_producto"], item["cantidad"]):
                        cur.execute(
                            "INSERT INTO detalle_venta (id_venta, id_producto, id_lote, cantidad, precio_unitario) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (id_venta, item["id_producto"], id_lote, cant, item["precio_unitario"]),
                        )
                        registrar_movimiento(cur, id_tienda, item["id_producto"], id_lote, "VENTA", cant,
                                             id_detalle_venta=cur.lastrowid)
            st.session_state["carrito_venta"] = []
            st.success(f"Venta #{id_venta} registrada. El inventario fue actualizado.")
            st.rerun()
        except Exception as error:
            st.error(f"No se pudo registrar la venta: {error}")
    if col2.button("Vaciar carrito"):
        st.session_state["carrito_venta"] = []
        st.rerun()
