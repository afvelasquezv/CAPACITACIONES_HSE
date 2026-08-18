import streamlit as st
import pandas as pd
import db
from views import coordinador  # Reutiliza las mismas funciones de gestión

def mostrar():
    st.title("👨‍💻 Panel de Administrador (Developer)")
    st.markdown("Gestión completa del sistema, incluyendo usuarios y roles.")

    tabs = st.tabs(["📋 Gestión General", "👥 Usuarios del Sistema"])

    with tabs[0]:
        # Reutiliza la vista del coordinador para empleados, clientes, cursos, asignaciones e indicadores
        coordinador.mostrar()

    with tabs[1]:
        st.subheader("Administración de Usuarios")
        conn = db.get_connection()
        usuarios_df = pd.read_sql_query("SELECT id, username, rol, nombre_completo, activo FROM usuarios", conn)
        conn.close()
        if not usuarios_df.empty:
            st.dataframe(usuarios_df, width='stretch', hide_index=True)
            with st.expander("Crear nuevo usuario"):
                new_username = st.text_input("Username")
                new_pass = st.text_input("Contraseña", type="password")
                new_rol = st.selectbox("Rol", ["coordinador", "admin", "empleado"])
                new_nombre = st.text_input("Nombre completo")
                if st.button("Crear usuario"):
                    if new_username and new_pass:
                        from werkzeug.security import generate_password_hash
                        hashed = generate_password_hash(new_pass)
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, 1)",
                                           (new_username, hashed, new_rol, new_nombre))
                            conn.commit()
                            st.success("Usuario creado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
                    else:
                        st.warning("Complete username y contraseña")
            with st.expander("Editar/Eliminar usuario"):
                user_seleccionado = st.selectbox("Usuario", usuarios_df['id'].tolist(),
                                                 format_func=lambda x: f"{usuarios_df[usuarios_df['id']==x]['username'].iloc[0]} ({usuarios_df[usuarios_df['id']==x]['rol'].iloc[0]})")
                if user_seleccionado:
                    user_row = usuarios_df[usuarios_df['id'] == user_seleccionado].iloc[0]
                    nuevo_nombre_completo = st.text_input("Nombre completo", value=user_row['nombre_completo'] if user_row['nombre_completo'] else "")
                    nuevo_rol = st.selectbox("Rol", ["coordinador", "admin", "empleado"], index=["coordinador","admin","empleado"].index(user_row['rol']))
                    activo = st.checkbox("Activo", value=bool(user_row['activo']))
                    nueva_pass = st.text_input("Nueva contraseña (dejar vacío para no cambiar)", type="password")
                    col_up, col_del = st.columns(2)
                    with col_up:
                        if st.button("Actualizar usuario"):
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            if nueva_pass:
                                from werkzeug.security import generate_password_hash
                                hashed = generate_password_hash(nueva_pass)
                                cursor.execute("UPDATE usuarios SET nombre_completo = ?, rol = ?, activo = ?, password_hash = ? WHERE id = ?",
                                               (nuevo_nombre_completo, nuevo_rol, 1 if activo else 0, hashed, user_seleccionado))
                            else:
                                cursor.execute("UPDATE usuarios SET nombre_completo = ?, rol = ?, activo = ? WHERE id = ?",
                                               (nuevo_nombre_completo, nuevo_rol, 1 if activo else 0, user_seleccionado))
                            conn.commit()
                            conn.close()
                            st.success("Usuario actualizado")
                            st.rerun()
                    with col_del:
                        if st.button("Eliminar usuario", type="primary"):
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_seleccionado,))
                            conn.commit()
                            conn.close()
                            st.success("Usuario eliminado")
                            st.rerun()
        else:
            st.info("No hay usuarios")