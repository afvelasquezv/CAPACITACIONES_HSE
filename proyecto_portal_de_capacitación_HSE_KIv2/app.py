import streamlit as st
import db
import os
import base64
import subprocess
from views import coordinador, admin, empleado
from pathlib import Path
import sys

# ------------------------------------------------------------
# Crear base de datos automáticamente si no existe
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "capacitaciones.db"
CREATION_SCRIPT = BASE_DIR / "db_master.py"

if not DB_PATH.exists():
    print("Base de datos no encontrada. Creando una nueva con datos de prueba...")

    try:
        subprocess.run(
            [sys.executable, str(CREATION_SCRIPT)],
            check=True
        )

        print("Base de datos creada exitosamente.")

    except subprocess.CalledProcessError as e:
        print(f"Error al crear la base de datos: {e}")
        st.error("No se pudo crear la base de datos. Contacta al administrador.")
        st.stop()

    except FileNotFoundError:
        print(f"No se encontró el script '{CREATION_SCRIPT}'")
        st.error(f"Falta el script de creación de la base de datos: {CREATION_SCRIPT}")
        st.stop()

st.set_page_config(
    page_title="Portal de Capacitaciones HSE",
    page_icon="assets/favicon_alkhorayef.png",
    layout="wide",
)

# app.py (después de st.set_page_config)
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True


LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo_alk.png")

def get_image_base64(path, default_text=""):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return default_text

def pagina_login():
    logo_base64 = get_image_base64(LOGO_PATH, "")
    if logo_base64:
        logo_html = f"""
        <div style="display: flex; justify-content: center; margin-top: 2rem; margin-bottom: 1rem;">
            <img src="data:image/png;base64,{logo_base64}" 
                 style="width: 150px; image-rendering: crisp-edges; image-rendering: high-quality;">
        </div>
        """
    else:
        logo_html = """
        <div style="display: flex; justify-content: center; margin-top: 2rem; margin-bottom: 1rem;">
            <div style="font-size: 4rem;">📚</div>
        </div>
        """
    st.markdown(logo_html, unsafe_allow_html=True)
    st.markdown(
        """
        <h1 style='text-align:center; margin-top:0;'>
            Portal de Capacitaciones HSE
        </h1>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p style='text-align:center; color:gray; margin-bottom: 2rem;'>
            Gestión y seguimiento de capacitaciones por cliente
        </p>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("---")
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submitted = st.form_submit_button("Ingresar", width='stretch')
        if submitted:
            usuario = db.autenticar_usuario(username, password)
            if usuario:
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos, o cuenta desactivada.")
        st.markdown("---")
        st.caption("¿Problemas de acceso? Contacta al administrador.")

def main():
    if "usuario" not in st.session_state:
        st.empty()
        pagina_login()
        return
    usuario = st.session_state.usuario
    with st.sidebar:
        logo_base64 = get_image_base64(LOGO_PATH, "")
        if logo_base64:
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 1rem;">
                    <img src="data:image/png;base64,{logo_base64}" 
                         style="width: 120px; image-rendering: crisp-edges; image-rendering: high-quality;">
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown("📊 **Capacitaciones HSE**")
        st.markdown(f"**👤 {usuario['nombre']}**")
        st.caption(f"Rol: {usuario['rol'].capitalize()}")
        st.divider()
        if st.button("🚪 Cerrar sesión", width='stretch'):
            del st.session_state.usuario
            st.rerun()

    rol = usuario["rol"]
    if rol == "coordinador":
        coordinador.mostrar()
    elif rol == "admin":
        admin.mostrar()
    elif rol == "empleado":
        empleado.mostrar(usuario)
    else:
        st.error("Rol no reconocido.")

if __name__ == "__main__":
    main()