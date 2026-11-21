import streamlit as st
import mysql.connector

from config.conexion import consultar, transaccion
from modulos.login import hash_contrasena
from modulos.utilidades import a_df


def mostrar_administracion():
    st.header("Administración")
    if st.session_state.get("rol") != "Administrador":
        st.error("No tiene permiso para acceder a este módulo.")
        return
    tab_t, tab_u, tab_c = st.tabs(["Tiendas", "Usuarios", "Categorías y unidades"])

    with tab_t:
        with st.form("form_tienda", clear_on_submit=True):
            nombre = st.text_input("Nombre de la tienda")
            direccion = st.text_input("Dirección")
            tipo = st.selectbox("Tipo", ["TIENDA", "CD"])
            guardar = st.form_submit_button("Guardar tienda")
        if guardar:
            if nombre.strip() == "":
                st.warning("Debe ingresar el nombre.")
            else:
                try:
                    with transaccion() as cur:
                        cur.execute("INSERT INTO tienda (nombre, direccion, tipo) VALUES (%s, %s, %s)",
                                    (nombre.strip(), direccion.strip() or None, tipo))
                    st.success("Tienda registrada.")
                except Exception as error:
                    st.error(f"No se pudo registrar: {error}")
        st.dataframe(a_df(consultar("SELECT id_tienda, nombre, direccion, tipo, estado FROM tienda ORDER BY id_tienda")),
                     hide_index=True)

    with tab_u:
        roles = consultar("SELECT id_rol, nombre FROM rol ORDER BY nombre")
        tiendas = consultar("SELECT id_tienda, nombre FROM tienda WHERE estado = TRUE ORDER BY nombre")
        if roles and tiendas:
            with st.form("form_usuario", clear_on_submit=True):
                nom = st.text_input("Nombre completo")
                usuario = st.text_input("Usuario")
                clave = st.text_input("Contraseña", type="password")
                r = st.selectbox("Rol", range(len(roles)), format_func=lambda i: roles[i]["nombre"])
                t = st.selectbox("Tienda", range(len(tiendas)), format_func=lambda i: tiendas[i]["nombre"])
                guardar = st.form_submit_button("Guardar usuario")
            if guardar:
                if nom.strip() == "" or usuario.strip() == "" or len(clave) < 6:
                    st.warning("Complete todos los campos. La contraseña debe tener al menos 6 caracteres.")
                else:
                    try:
                        with transaccion() as cur:
                            cur.execute(
                                "INSERT INTO usuario (nombre, usuario, contrasena_hash, id_rol, id_tienda) "
                                "VALUES (%s, %s, %s, %s, %s)",
                                (nom.strip(), usuario.strip(), hash_contrasena(clave),
                                 roles[r]["id_rol"], tiendas[t]["id_tienda"]),
                            )
                        st.success("Usuario registrado.")
                    except mysql.connector.IntegrityError:
                        st.error("Ese nombre de usuario ya existe.")
                    except Exception as error:
                        st.error(f"No se pudo registrar: {error}")
        st.dataframe(a_df(consultar(
            """
            SELECT u.id_usuario, u.nombre, u.usuario, r.nombre AS rol, t.nombre AS tienda
            FROM usuario u INNER JOIN rol r ON r.id_rol = u.id_rol
            INNER JOIN tienda t ON t.id_tienda = u.id_tienda ORDER BY u.id_usuario
            """)), hide_index=True)

    with tab_c:
        col1, col2 = st.columns(2)
        with col1:
            with st.form("form_categoria", clear_on_submit=True):
                cat = st.text_input("Nueva categoría")
                g1 = st.form_submit_button("Guardar categoría")
            if g1 and cat.strip():
                try:
                    with transaccion() as cur:
                        cur.execute("INSERT INTO categoria (nombre) VALUES (%s)", (cat.strip(),))
                    st.success("Categoría registrada.")
                except mysql.connector.IntegrityError:
                    st.error("La categoría ya existe.")
            st.dataframe(a_df(consultar("SELECT id_categoria, nombre FROM categoria ORDER BY nombre")), hide_index=True)
        with col2:
            with st.form("form_unidad", clear_on_submit=True):
                un = st.text_input("Nueva unidad")
                ab = st.text_input("Abreviatura")
                g2 = st.form_submit_button("Guardar unidad")
            if g2 and un.strip() and ab.strip():
                try:
                    with transaccion() as cur:
                        cur.execute("INSERT INTO unidad_medida (nombre, abreviatura) VALUES (%s, %s)",
                                    (un.strip(), ab.strip()))
                    st.success("Unidad registrada.")
                except mysql.connector.IntegrityError:
                    st.error("La unidad ya existe.")
            st.dataframe(a_df(consultar("SELECT id_unidad, nombre, abreviatura FROM unidad_medida ORDER BY nombre")),
                         hide_index=True)
