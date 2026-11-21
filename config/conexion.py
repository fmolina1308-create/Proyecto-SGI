from contextlib import contextmanager

import mysql.connector
import streamlit as st


def obtener_conexion():
    """Abre una conexión usando las credenciales de Streamlit Secrets."""
    try:
        return mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
        )
    except mysql.connector.Error as error:
        st.error(f"Error al conectar con la base de datos: {error}")
        return None


def consultar(sql, params=None):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    conexion = obtener_conexion()
    if conexion is None:
        return []
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    except Exception as error:
        st.error(f"Error en la consulta: {error}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conexion.is_connected():
            conexion.close()


@contextmanager
def transaccion():
    """Agrupa varias instrucciones: si una falla se revierte todo (rollback)."""
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No hay conexión con la base de datos.")
    cursor = conexion.cursor(dictionary=True)
    try:
        yield cursor
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        if conexion.is_connected():
            conexion.close()
