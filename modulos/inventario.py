import streamlit as st

from config.conexion import consultar
from modulos.utilidades import a_df, selector_tienda


def mostrar_inventario():
    st.header("Inventario")
    id_tienda = selector_tienda("inv_tienda")
    filtro = "" if id_tienda is None else "AND i.id_tienda = %s"
    params = () if id_tienda is None else (id_tienda,)

    tab_exist, tab_bajo, tab_venc = st.tabs(["Existencias", "Stock bajo", "Próximos a vencer"])

    existencias = consultar(
        f"""
        SELECT t.nombre AS tienda, p.nombre AS producto, c.nombre AS categoria, u.abreviatura AS unidad,
               i.existencia, i.stock_minimo, i.precio_venta
        FROM inventario i
        INNER JOIN tienda t ON t.id_tienda = i.id_tienda
        INNER JOIN producto p ON p.id_producto = i.id_producto
        INNER JOIN categoria c ON c.id_categoria = p.id_categoria
        INNER JOIN unidad_medida u ON u.id_unidad = p.id_unidad
        WHERE 1 = 1 {filtro}
        ORDER BY t.nombre, p.nombre
        """,
        params,
    )

    with tab_exist:
        if existencias:
            st.dataframe(a_df(existencias), hide_index=True)
        else:
            st.info("No hay existencias registradas.")

    with tab_bajo:
        bajo = [f for f in existencias if float(f["existencia"]) <= float(f["stock_minimo"])]
        if bajo:
            st.warning(f"{len(bajo)} producto(s) en o por debajo del stock mínimo.")
            st.dataframe(a_df(bajo), hide_index=True)
        else:
            st.success("Ningún producto está por debajo del stock mínimo.")

    with tab_venc:
        dias = st.number_input("Mostrar lotes que vencen en los próximos (días)", min_value=1, value=30, step=1)
        filtro_l = "" if id_tienda is None else "AND l.id_tienda = %s"
        params_l = (int(dias),) if id_tienda is None else (int(dias), id_tienda)
        lotes = consultar(
            f"""
            SELECT t.nombre AS tienda, p.nombre AS producto, l.id_lote, l.fecha_vencimiento,
                   DATEDIFF(l.fecha_vencimiento, CURDATE()) AS dias_restantes, l.cantidad_disponible
            FROM lote l
            INNER JOIN tienda t ON t.id_tienda = l.id_tienda
            INNER JOIN producto p ON p.id_producto = l.id_producto
            WHERE l.fecha_vencimiento IS NOT NULL AND l.cantidad_disponible > 0
              AND l.fecha_vencimiento <= DATE_ADD(CURDATE(), INTERVAL %s DAY) {filtro_l}
            ORDER BY l.fecha_vencimiento
            """,
            params_l,
        )
        if lotes:
            st.warning(f"{len(lotes)} lote(s) vencen en los próximos {int(dias)} días o ya vencieron.")
            st.dataframe(a_df(lotes), hide_index=True)
        else:
            st.success("No hay lotes próximos a vencer en ese período.")
