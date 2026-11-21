import streamlit as st

from config.conexion import consultar, transaccion
from modulos.utilidades import (a_df, consumir_lotes, registrar_movimiento, restar_inventario,
                                sumar_inventario, ui_carrito)
from modulos.ventas import productos_disponibles


def mostrar_envios():
    es_cd = st.session_state["tipo_tienda"] == "CD"
    st.header("Despachos del Centro de Distribución" if es_cd else "Envíos del Centro de Distribución")
    if es_cd:
        tab_nuevo, tab_hist = st.tabs(["Nuevo despacho", "Despachos realizados"])
        with tab_nuevo:
            nuevo_despacho()
        with tab_hist:
            historial_despachos()
    else:
        recibir_envios()


def nuevo_despacho():
    id_cd = st.session_state["id_tienda"]
    destinos = consultar("SELECT id_tienda, nombre FROM tienda WHERE tipo = 'TIENDA' AND estado = TRUE ORDER BY nombre")
    productos = productos_disponibles(id_cd)
    if not destinos:
        st.warning("No hay tiendas activas registradas.")
        return
    if not productos:
        st.info("El CD no tiene productos con existencia y precio definido.")
        return
    dest = st.selectbox("Tienda destino", range(len(destinos)), format_func=lambda i: destinos[i]["nombre"])
    st.caption("La salida se registra en el CD ahora. La tienda registrará su compra cuando reciba físicamente el producto.")
    carrito, total = ui_carrito("carrito_despacho", productos)

    col1, col2 = st.columns(2)
    if col1.button("Registrar despacho", disabled=not carrito):
        try:
            with transaccion() as cur:
                cur.execute(
                    """
                    INSERT INTO venta (id_tienda, id_tienda_destino, id_usuario, tipo_venta, estado, fecha_envio, total)
                    VALUES (%s, %s, %s, 'DESPACHO_CD', 'EN_TRANSITO', NOW(), %s)
                    """,
                    (id_cd, destinos[dest]["id_tienda"], st.session_state["id_usuario"], total),
                )
                id_venta = cur.lastrowid
                for item in carrito:
                    restar_inventario(cur, id_cd, item["id_producto"], item["cantidad"])
                    for id_lote, cant in consumir_lotes(cur, id_cd, item["id_producto"], item["cantidad"]):
                        cur.execute(
                            "INSERT INTO detalle_venta (id_venta, id_producto, id_lote, cantidad, precio_unitario) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (id_venta, item["id_producto"], id_lote, cant, item["precio_unitario"]),
                        )
                        registrar_movimiento(cur, id_cd, item["id_producto"], id_lote, "ENVIO", cant,
                                             id_detalle_venta=cur.lastrowid)
            st.session_state["carrito_despacho"] = []
            st.success(f"Despacho #{id_venta} registrado y en tránsito hacia {destinos[dest]['nombre']}.")
            st.rerun()
        except Exception as error:
            st.error(f"No se pudo registrar el despacho: {error}")
    if col2.button("Vaciar despacho"):
        st.session_state["carrito_despacho"] = []
        st.rerun()


def historial_despachos():
    filas = consultar(
        """
        SELECT v.id_venta AS despacho, t.nombre AS destino, v.estado, v.fecha_envio, v.fecha_recepcion, v.total
        FROM venta v INNER JOIN tienda t ON t.id_tienda = v.id_tienda_destino
        WHERE v.tipo_venta = 'DESPACHO_CD' AND v.id_tienda = %s
        ORDER BY v.id_venta DESC
        """,
        (st.session_state["id_tienda"],),
    )
    if filas:
        st.dataframe(a_df(filas), hide_index=True)
    else:
        st.info("Aún no se han realizado despachos.")


def recibir_envios():
    id_tienda = st.session_state["id_tienda"]
    pendientes = consultar(
        """
        SELECT v.id_venta, v.fecha_envio, v.total, t.nombre AS origen
        FROM venta v INNER JOIN tienda t ON t.id_tienda = v.id_tienda
        WHERE v.tipo_venta = 'DESPACHO_CD' AND v.estado = 'EN_TRANSITO' AND v.id_tienda_destino = %s
        ORDER BY v.id_venta
        """,
        (id_tienda,),
    )
    st.subheader("Envíos por recibir")
    if not pendientes:
        st.info("No hay envíos en tránsito hacia su tienda.")
    for env in pendientes:
        with st.expander(f"Envío #{env['id_venta']} desde {env['origen']} | total ${float(env['total']):,.2f}"):
            detalle = consultar(
                """
                SELECT p.nombre AS producto, SUM(dv.cantidad) AS cantidad, dv.precio_unitario, l.fecha_vencimiento
                FROM detalle_venta dv
                INNER JOIN producto p ON p.id_producto = dv.id_producto
                LEFT JOIN lote l ON l.id_lote = dv.id_lote
                WHERE dv.id_venta = %s
                GROUP BY p.nombre, dv.precio_unitario, l.fecha_vencimiento
                """,
                (env["id_venta"],),
            )
            st.dataframe(a_df(detalle), hide_index=True)
            if st.button("Confirmar recepción física", key=f"rec_{env['id_venta']}"):
                try:
                    confirmar_recepcion(env["id_venta"], id_tienda)
                    st.success("Recepción confirmada. Se registró la compra y se actualizó el inventario.")
                    st.rerun()
                except Exception as error:
                    st.error(f"No se pudo confirmar la recepción: {error}")

    st.subheader("Historial de envíos recibidos")
    hist = consultar(
        """
        SELECT v.id_venta AS envio, v.fecha_envio, v.fecha_recepcion, v.total
        FROM venta v WHERE v.tipo_venta = 'DESPACHO_CD' AND v.estado = 'RECIBIDO' AND v.id_tienda_destino = %s
        ORDER BY v.id_venta DESC
        """,
        (id_tienda,),
    )
    if hist:
        st.dataframe(a_df(hist), hide_index=True)


def confirmar_recepcion(id_venta, id_tienda):
    with transaccion() as cur:
        cur.execute(
            "SELECT id_venta, total FROM venta WHERE id_venta = %s AND estado = 'EN_TRANSITO' "
            "AND id_tienda_destino = %s FOR UPDATE",
            (id_venta, id_tienda),
        )
        envio = cur.fetchone()
        if not envio:
            raise ValueError("El envío ya fue recibido o no corresponde a su tienda.")
        cur.execute(
            "INSERT INTO compra (id_tienda, id_proveedor, id_venta_origen, id_usuario, total) "
            "VALUES (%s, NULL, %s, %s, %s)",
            (id_tienda, id_venta, st.session_state["id_usuario"], envio["total"]),
        )
        id_compra = cur.lastrowid
        cur.execute(
            """
            SELECT dv.id_producto, dv.cantidad, dv.precio_unitario, l.fecha_vencimiento
            FROM detalle_venta dv LEFT JOIN lote l ON l.id_lote = dv.id_lote
            WHERE dv.id_venta = %s
            """,
            (id_venta,),
        )
        for d in cur.fetchall():
            cantidad = float(d["cantidad"])
            id_lote = None
            if d["fecha_vencimiento"] is not None:
                cur.execute(
                    "INSERT INTO lote (id_tienda, id_producto, fecha_vencimiento, cantidad_disponible) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_tienda, d["id_producto"], d["fecha_vencimiento"], cantidad),
                )
                id_lote = cur.lastrowid
            cur.execute(
                "INSERT INTO detalle_compra (id_compra, id_producto, id_lote, cantidad, precio_compra) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_compra, d["id_producto"], id_lote, cantidad, d["precio_unitario"]),
            )
            id_detalle = cur.lastrowid
            sumar_inventario(cur, id_tienda, d["id_producto"], cantidad)
            registrar_movimiento(cur, id_tienda, d["id_producto"], id_lote, "COMPRA", cantidad,
                                 id_detalle_compra=id_detalle)
        cur.execute(
            "UPDATE venta SET estado = 'RECIBIDO', fecha_recepcion = NOW() WHERE id_venta = %s",
            (id_venta,),
        )
