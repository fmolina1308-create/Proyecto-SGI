from decimal import Decimal

import pandas as pd
import streamlit as st

from config.conexion import consultar


def a_df(filas):
    """Convierte filas de MySQL en DataFrame (Decimal a float)."""
    if not filas:
        return pd.DataFrame()
    df = pd.DataFrame(filas)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


def boton_csv(df, nombre_archivo, clave):
    """Botón para descargar una tabla en CSV (compatible con Excel)."""
    if df is not None and not df.empty:
        st.download_button(
            "Descargar CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name=nombre_archivo,
            mime="text/csv",
            key=clave,
        )


def filtrar_texto(df, columna, texto):
    """Filtra un DataFrame por texto (sin distinguir mayúsculas)."""
    if df is None or df.empty or not texto or not str(texto).strip():
        return df
    return df[df[columna].astype(str).str.contains(str(texto).strip(), case=False, na=False, regex=False)]


def puede_ver_global():
    """El administrador y el CD tienen vision global; las tiendas solo la suya."""
    return (
        st.session_state.get("rol") == "Administrador"
        or st.session_state.get("tipo_tienda") == "CD"
    )


def selector_tienda(clave):
    """Devuelve id_tienda (o None = todas) segun los permisos del usuario."""
    if not puede_ver_global():
        return st.session_state["id_tienda"]
    tiendas = consultar("SELECT id_tienda, nombre FROM tienda WHERE estado = TRUE ORDER BY nombre")
    nombres = {t["id_tienda"]: t["nombre"] for t in tiendas}
    opciones = [None] + list(nombres.keys())
    return st.selectbox(
        "Tienda",
        opciones,
        format_func=lambda x: "Todas las tiendas" if x is None else nombres[x],
        key=clave,
    )


# ---------- Operaciones de inventario (se usan dentro de una transaccion) ----------
def sumar_inventario(cur, id_tienda, id_producto, cantidad, precio_venta=None):
    cur.execute(
        """
        INSERT INTO inventario (id_tienda, id_producto, existencia, precio_venta)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            existencia = existencia + VALUES(existencia),
            precio_venta = COALESCE(VALUES(precio_venta), precio_venta)
        """,
        (id_tienda, id_producto, cantidad, precio_venta),
    )


def restar_inventario(cur, id_tienda, id_producto, cantidad):
    cur.execute(
        "SELECT existencia FROM inventario WHERE id_tienda = %s AND id_producto = %s FOR UPDATE",
        (id_tienda, id_producto),
    )
    fila = cur.fetchone()
    if not fila or float(fila["existencia"]) < cantidad:
        raise ValueError("Existencia insuficiente para completar la operación.")
    cur.execute(
        "UPDATE inventario SET existencia = existencia - %s WHERE id_tienda = %s AND id_producto = %s",
        (cantidad, id_tienda, id_producto),
    )


def consumir_lotes(cur, id_tienda, id_producto, cantidad):
    """Descuenta primero los lotes que vencen antes (FEFO). Devuelve [(id_lote, cantidad)]."""
    cur.execute(
        """
        SELECT id_lote, cantidad_disponible FROM lote
        WHERE id_tienda = %s AND id_producto = %s AND cantidad_disponible > 0
        ORDER BY (fecha_vencimiento IS NULL), fecha_vencimiento, id_lote
        FOR UPDATE
        """,
        (id_tienda, id_producto),
    )
    restante = float(cantidad)
    tomados = []
    for lote in cur.fetchall():
        if restante <= 0:
            break
        tomar = min(float(lote["cantidad_disponible"]), restante)
        cur.execute(
            "UPDATE lote SET cantidad_disponible = cantidad_disponible - %s WHERE id_lote = %s",
            (tomar, lote["id_lote"]),
        )
        tomados.append((lote["id_lote"], tomar))
        restante -= tomar
    if restante > 1e-9:
        tomados.append((None, restante))
    return tomados


def registrar_movimiento(cur, id_tienda, id_producto, id_lote, tipo, cantidad,
                         id_detalle_compra=None, id_detalle_venta=None):
    cur.execute(
        """
        INSERT INTO movimiento_inventario
            (id_tienda, id_producto, id_lote, id_usuario, id_detalle_compra,
             id_detalle_venta, tipo, cantidad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (id_tienda, id_producto, id_lote, st.session_state["id_usuario"],
         id_detalle_compra, id_detalle_venta, tipo, cantidad),
    )


def ui_carrito(clave, productos):
    """Formulario para agregar productos a un carrito. Devuelve (carrito, total)."""
    carrito = st.session_state.setdefault(clave, [])
    with st.form(f"form_{clave}", clear_on_submit=True):
        idx = st.selectbox(
            "Producto",
            range(len(productos)),
            format_func=lambda i: (
                f"{productos[i]['nombre']} | existencia: {float(productos[i]['existencia']):g} "
                f"{productos[i]['abreviatura']} | precio: ${float(productos[i]['precio_venta']):.2f}"
            ),
        )
        cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0)
        agregar = st.form_submit_button("Agregar al carrito")
    if agregar:
        p = productos[idx]
        ya = sum(l["cantidad"] for l in carrito if l["id_producto"] == p["id_producto"])
        if ya + cantidad > float(p["existencia"]):
            st.warning("La cantidad supera la existencia disponible.")
        else:
            carrito.append({
                "id_producto": p["id_producto"],
                "producto": p["nombre"],
                "cantidad": float(cantidad),
                "precio_unitario": float(p["precio_venta"]),
            })
    total = 0.0
    if carrito:
        df = a_df(carrito)
        df["subtotal"] = df["cantidad"] * df["precio_unitario"]
        total = float(df["subtotal"].sum())
        st.dataframe(df[["producto", "cantidad", "precio_unitario", "subtotal"]], hide_index=True)
        st.write(f"**Total: ${total:,.2f}**")
    return carrito, round(total, 2)
