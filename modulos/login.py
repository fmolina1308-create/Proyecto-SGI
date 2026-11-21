import hashlib

import streamlit as st

from config.conexion import consultar


def hash_contrasena(contrasena):
    return hashlib.sha256(contrasena.encode("utf-8")).hexdigest()


def verificar_usuario(usuario, contrasena):
    filas = consultar(
        """
        SELECT u.id_usuario, u.nombre, u.usuario, r.nombre AS rol,
               u.id_tienda, t.nombre AS tienda, t.tipo AS tipo_tienda, t.estado
        FROM usuario u
        INNER JOIN rol r ON r.id_rol = u.id_rol
        INNER JOIN tienda t ON t.id_tienda = u.id_tienda
        WHERE u.usuario = %s AND u.contrasena_hash = %s
        LIMIT 1
        """,
        (usuario, hash_contrasena(contrasena)),
    )
    return filas[0] if filas else None


def login():
    st.title("Inicio de sesión")
    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if usuario.strip() == "" or contrasena.strip() == "":
            st.warning("Ingrese su usuario y contraseña.")
            return
        datos = verificar_usuario(usuario.strip(), contrasena)
        if not datos:
            st.error("Usuario o contraseña incorrectos.")
        elif not datos["estado"]:
            st.error("La tienda asignada a este usuario está inactiva.")
        else:
            st.session_state["sesion_iniciada"] = True
            st.session_state["usuario"] = datos["usuario"]
            st.session_state["id_usuario"] = datos["id_usuario"]
            st.session_state["nombre"] = datos["nombre"]
            st.session_state["rol"] = datos["rol"]
            st.session_state["id_tienda"] = datos["id_tienda"]
            st.session_state["tienda"] = datos["tienda"]
            st.session_state["tipo_tienda"] = datos["tipo_tienda"]
            st.rerun()
