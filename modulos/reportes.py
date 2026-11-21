from datetime import date, timedelta

import streamlit as st

from config.conexion import consultar
from modulos.utilidades import a_df, selector_tienda


def mostrar_reportes():
    st.header("Reportes")
    id_tienda = selector_tienda("rep_tienda")
    t_ventas = "" if id_tienda is None else "AND v.id_tienda = %s"
    t_compras = "" if id_tienda is None else "AND c.id_tienda = %s"
    p_tienda = () if id_tienda is None else (id_tienda,)

    tab_mov, tab_prod, tab_tienda, tab_comprar, tab_cd = st.tabs(
        ["Compras y ventas", "Comportamiento de productos", "Resumen por tienda",
         "Cuándo y cuánto comprar", "¿Conviene comprar al CD?"]
    )

    with tab_mov:
        c1, c2 = st.columns(2)
        desde = c1.date_input("Desde", value=date.today() - timedelta(days=30), key="rep_desde")
        hasta = c2.date_input("Hasta", value=date.today(), key="rep_hasta")
        ventas = consultar(
            f"""
            SELECT v.id_venta, t.nombre AS tienda, v.tipo_venta, v.fecha, p.nombre AS producto,
                   dv.cantidad, dv.precio_unitario, dv.cantidad * dv.precio_unitario AS subtotal
            FROM venta v
            INNER JOIN tienda t ON t.id_tienda = v.id_tienda
            INNER JOIN detalle_venta dv ON dv.id_venta = v.id_venta
            INNER JOIN producto p ON p.id_producto = dv.id_producto
            WHERE DATE(v.fecha) BETWEEN %s AND %s {t_ventas}
            ORDER BY v.fecha DESC
            """,
            (desde, hasta) + p_tienda,
        )
        compras = consultar(
            f"""
            SELECT c.id_compra, t.nombre AS tienda, COALESCE(pr.nombre, 'Centro de Distribución') AS proveedor,
                   c.fecha, p.nombre AS producto, dc.cantidad, dc.precio_compra,
                   dc.cantidad * dc.precio_compra AS subtotal
            FROM compra c
            INNER JOIN tienda t ON t.id_tienda = c.id_tienda
            LEFT JOIN proveedor pr ON pr.id_proveedor = c.id_proveedor
            INNER JOIN detalle_compra dc ON dc.id_compra = c.id_compra
            INNER JOIN producto p ON p.id_producto = dc.id_producto
            WHERE DATE(c.fecha) BETWEEN %s AND %s {t_compras}
            ORDER BY c.fecha DESC
            """,
            (desde, hasta) + p_tienda,
        )
        df_v, df_c = a_df(ventas), a_df(compras)
        st.subheader("Ventas")
        if df_v.empty:
            st.info("No hay ventas en el período.")
        else:
            st.dataframe(df_v, hide_index=True)
            st.write(f"**Total vendido: ${df_v['subtotal'].sum():,.2f}**")
        st.subheader("Compras")
        if df_c.empty:
            st.info("No hay compras en el período.")
        else:
            st.dataframe(df_c, hide_index=True)
            st.write(f"**Total comprado: ${df_c['subtotal'].sum():,.2f}**")

    with tab_prod:
        vc = df_v[df_v["tipo_venta"] == "VENTA_CLIENTE"] if not df_v.empty else df_v
        if vc.empty:
            st.info("No hay ventas a clientes en el período seleccionado en la pestaña anterior.")
        else:
            top = (vc.groupby("producto").agg(unidades=("cantidad", "sum"), ingresos=("subtotal", "sum"))
                     .sort_values("unidades", ascending=False))
            st.caption("Productos más vendidos en el período elegido en 'Compras y ventas'.")
            st.bar_chart(top["unidades"])
            st.dataframe(top.reset_index())
            sin_ventas = consultar(
                f"""
                SELECT p.nombre AS producto, i.existencia FROM inventario i
                INNER JOIN producto p ON p.id_producto = i.id_producto
                WHERE i.existencia > 0 {"" if id_tienda is None else "AND i.id_tienda = %s"}
                """,
                p_tienda,
            )
            nombres_vendidos = set(top.index)
            lentos = [f for f in sin_ventas if f["producto"] not in nombres_vendidos]
            if lentos:
                st.subheader("Productos con existencia y sin ventas en el período")
                st.dataframe(a_df(lentos), hide_index=True)

    with tab_tienda:
        partes = []
        if not df_v.empty:
            partes.append(df_v.groupby("tienda")["subtotal"].sum().rename("ventas"))
        if not df_c.empty:
            partes.append(df_c.groupby("tienda")["subtotal"].sum().rename("compras"))
        if partes:
            import pandas as pd
            res = pd.concat(partes, axis=1).fillna(0)
            st.dataframe(res.reset_index())
            st.bar_chart(res)
        else:
            st.info("No hay movimientos en el período.")

    with tab_comprar:
        st.caption("Punto de reorden = demanda diaria × días de reposición + stock mínimo.")
        c1, c2, c3 = st.columns(3)
        hist = c1.number_input("Días de historial de ventas", min_value=7, value=30, step=1)
        repos = c2.number_input("Días de reposición del proveedor", min_value=1, value=7, step=1)
        cobertura = c3.number_input("Días de cobertura deseada", min_value=1, value=15, step=1)
        filas = consultar(
            f"""
            SELECT t.nombre AS tienda, p.nombre AS producto, i.existencia, i.stock_minimo,
                   COALESCE(vv.vendido, 0) AS vendido
            FROM inventario i
            INNER JOIN tienda t ON t.id_tienda = i.id_tienda
            INNER JOIN producto p ON p.id_producto = i.id_producto
            LEFT JOIN (
                SELECT v.id_tienda, dv.id_producto, SUM(dv.cantidad) AS vendido
                FROM venta v INNER JOIN detalle_venta dv ON dv.id_venta = v.id_venta
                WHERE v.tipo_venta = 'VENTA_CLIENTE' AND v.fecha >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY v.id_tienda, dv.id_producto
            ) vv ON vv.id_tienda = i.id_tienda AND vv.id_producto = i.id_producto
            WHERE 1 = 1 {"" if id_tienda is None else "AND i.id_tienda = %s"}
            ORDER BY t.nombre, p.nombre
            """,
            (int(hist),) + p_tienda,
        )
        df = a_df(filas)
        if df.empty:
            st.info("No hay inventario para analizar.")
        else:
            df["demanda_diaria"] = (df["vendido"] / hist).round(2)
            df["punto_reorden"] = (df["demanda_diaria"] * repos + df["stock_minimo"]).round(2)
            objetivo = df["demanda_diaria"] * (repos + cobertura) + df["stock_minimo"]
            df["cantidad_sugerida"] = (objetivo - df["existencia"]).clip(lower=0).round(0)
            df["decision"] = df.apply(
                lambda f: "Comprar ahora" if f["existencia"] <= f["punto_reorden"] else "No comprar", axis=1)
            solo = st.checkbox("Mostrar solo los productos que hay que comprar", value=True)
            vista = df[df["decision"] == "Comprar ahora"] if solo else df
            st.dataframe(vista[["tienda", "producto", "existencia", "demanda_diaria", "punto_reorden",
                                "cantidad_sugerida", "decision"]], hide_index=True)

    with tab_cd:
        st.caption("El CD es proveedor de una tienda solo si su costo global de adquisición es menor.")
        filas = consultar(
            f"""
            SELECT p.nombre AS producto,
              (SELECT SUM(dc.cantidad * dc.precio_compra) / SUM(dc.cantidad)
                 FROM detalle_compra dc
                 INNER JOIN compra c ON c.id_compra = dc.id_compra
                 INNER JOIN tienda tc ON tc.id_tienda = c.id_tienda
                 WHERE tc.tipo = 'CD' AND dc.id_producto = p.id_producto) AS costo_cd,
              (SELECT MIN(pp.ultimo_precio) FROM producto_proveedor pp
                 INNER JOIN proveedor pr ON pr.id_proveedor = pp.id_proveedor
                 WHERE pp.id_producto = p.id_producto
                 {"" if id_tienda is None else "AND pr.id_tienda = %s"}) AS mejor_precio_proveedor
            FROM producto p
            ORDER BY p.nombre
            """,
            p_tienda,
        )
        df = a_df(filas)
        if df.empty:
            st.info("No hay productos.")
        else:
            def evaluar(f):
                if f["costo_cd"] != f["costo_cd"] or f["mejor_precio_proveedor"] != f["mejor_precio_proveedor"]:
                    return "Sin datos suficientes"
                return "Sí, el CD es más barato" if f["costo_cd"] < f["mejor_precio_proveedor"] else "No, conviene el proveedor"
            df["conviene_comprar_al_cd"] = df.apply(evaluar, axis=1)
            st.dataframe(df.round(2), hide_index=True)
