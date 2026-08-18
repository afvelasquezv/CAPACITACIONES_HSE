import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import db

def mostrar(usuario):
    st.title(f"👤 Bienvenido, {usuario['nombre']}")
    st.markdown("Consulta tus capacitaciones asignadas y tu progreso")

    # Obtener el id del empleado a partir del username (cédula)
    username = usuario['username']
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM empleados WHERE cedula = ?", (username,))
    empleado_row = cursor.fetchone()
    conn.close()
    if not empleado_row:
        st.error("No se encontró información de empleado asociada a tu usuario.")
        return
    empleado_id = empleado_row[0]

    # Obtener datos
    asignaciones = db.obtener_asignaciones(empleado_id)
    indicadores = db.obtener_indicadores_empleado(empleado_id)

    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total cursos asignados", indicadores['total'])
    col2.metric("Completados", indicadores['completados'])
    col3.metric("Cumplimiento", f"{indicadores['porcentaje']}%")
    col4.metric("Por renovar", indicadores['por_renovar'])

    st.markdown("---")
    if not asignaciones.empty:
        # Convertir columnas de fecha a datetime
        asignaciones['fecha_asignacion'] = pd.to_datetime(asignaciones['fecha_asignacion']).dt.date
        asignaciones['fecha_vencimiento'] = pd.to_datetime(asignaciones['fecha_vencimiento']).dt.date

        hoy = date.today()
        limite = hoy + timedelta(days=30)

        # Determinar si es sin vencimiento (fecha >= 9999-12-31)
        asignaciones['es_sin_vencimiento'] = asignaciones['fecha_vencimiento'].apply(lambda x: x.year >= 9999)

        # Formatear fechas
        asignaciones['fecha_vencimiento_mostrar'] = asignaciones.apply(
            lambda row: "Sin vencimiento" if row['es_sin_vencimiento'] else row['fecha_vencimiento'].strftime("%d/%m/%Y"),
            axis=1
        )
        asignaciones['fecha_asignacion_mostrar'] = asignaciones['fecha_asignacion'].apply(lambda x: x.strftime("%d/%m/%Y"))

        # Estado personalizado
        def formatear_estado(row):
            if row['es_sin_vencimiento']:
                return "Sin vencimiento"
            if row['fecha_vencimiento'] < hoy:
                return "Vencido"
            if row['fecha_vencimiento'] <= limite:
                return "Próximo a vencer"
            return "Vigente"

        asignaciones['estado_mostrar'] = asignaciones.apply(formatear_estado, axis=1)

        # ============================================================
        # SISTEMA DE ALARMA CON CAMPANA 🔔
        # ============================================================

        alertas_vencidos = asignaciones[asignaciones['estado_mostrar'] == 'Vencido']
        alertas_proximos = asignaciones[asignaciones['estado_mostrar'] == 'Próximo a vencer']

        total_alertas = len(alertas_vencidos) + len(alertas_proximos)

        # Determinar nivel de alerta
        if len(alertas_vencidos) > 0:
            nivel_alerta = "crítico"
            color_alerta = "#ff4444"
            emoji_alerta = "🔴"
        elif len(alertas_proximos) > 0:
            nivel_alerta = "advertencia"
            color_alerta = "#ff8800"
            emoji_alerta = "🟠"
        else:
            nivel_alerta = "ok"
            color_alerta = "#00cc66"
            emoji_alerta = "🟢"

        if total_alertas > 0:
            # Sonido de alerta
            if nivel_alerta in ["crítico", "advertencia"]:
                st.markdown(
                    '<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>',
                    unsafe_allow_html=True
                )

            # Construir texto del banner de forma robusta
            partes_banner = []
            if len(alertas_vencidos) > 0:
                partes_banner.append(f"<b>{len(alertas_vencidos)}</b> vencida{'s' if len(alertas_vencidos) > 1 else ''}")
            if len(alertas_proximos) > 0:
                partes_banner.append(f"<b>{len(alertas_proximos)}</b> próxima{'s' if len(alertas_proximos) > 1 else ''} a vencer")

            texto_banner = " • ".join(partes_banner)
            palabra_alerta = "alertas" if total_alertas > 1 else "alerta"

            # Banner HTML limpio (una sola línea para evitar saltos en atributos)
            banner_html = (
                f'<div style="background: linear-gradient(135deg, {color_alerta}22, {color_alerta}11); '
                f'border-left: 5px solid {color_alerta}; border-radius: 10px; padding: 15px 20px; '
                f'margin-bottom: 20px; display: flex; align-items: center; gap: 15px;">'
                f'<div style="font-size: 32px;">🔔</div>'
                f'<div style="flex: 1;">'
                f'<div style="font-size: 18px; font-weight: bold; color: {color_alerta};">'
                f'{emoji_alerta} Sistema de Alertas — {total_alertas} {palabra_alerta} activas'
                f'</div>'
                f'<div style="color: #666; margin-top: 4px;">{texto_banner}</div>'
                f'</div></div>'
            )

            st.markdown(banner_html, unsafe_allow_html=True)

            # Panel de alertas detalladas
            with st.expander("📋 Ver detalle de alertas", expanded=(nivel_alerta == "crítico")):
                if len(alertas_vencidos) > 0:
                    st.error("⚠️ Capacitaciones VENCIDAS — Requiere acción inmediata")
                    for _, row in alertas_vencidos.iterrows():
                        st.markdown(
                            f'<div style="background: #ffebee; border-radius: 8px; padding: 10px 15px; '
                            f'margin: 5px 0; border-left: 4px solid #f44336;">'
                            f'<b>🔴 {row["curso"]}</b> — Cliente: {row["cliente"]}<br>'
                            f'<small>Venció el: {row["fecha_vencimiento_mostrar"]}</small></div>',
                            unsafe_allow_html=True
                        )

                if len(alertas_proximos) > 0:
                    st.warning("⏰ Próximas a vencer — Tienes 30 días o menos")
                    for _, row in alertas_proximos.iterrows():
                        dias_restantes = (row['fecha_vencimiento'] - hoy).days
                        st.markdown(
                            f'<div style="background: #fff3e0; border-radius: 8px; padding: 10px 15px; '
                            f'margin: 5px 0; border-left: 4px solid #ff9800;">'
                            f'<b>🟠 {row["curso"]}</b> — Cliente: {row["cliente"]}<br>'
                            f'<small>Vence el: {row["fecha_vencimiento_mostrar"]} (quedan <b>{dias_restantes} días</b>)</small></div>',
                            unsafe_allow_html=True
                        )

        else:
            st.success("✅ Todo en orden — No tienes alertas pendientes")

        # ============================================================

        # Gráfico de pastel con colores fijos por estado
        estado_counts = asignaciones['estado_mostrar'].value_counts().reset_index()
        estado_counts.columns = ['Estado', 'Cantidad']

        # Mapeo de colores: cada estado siempre tiene el mismo color
        color_map = {
            "Vencido": "#ff4444",
            "Próximo a vencer": "#ff8800",
            "Vigente": "#00cc66",
            "Sin vencimiento": "#9e9e9e"
        }

        fig = px.pie(
            estado_counts,
            values='Cantidad',
            names='Estado',
            title="Distribución de tus capacitaciones",
            color='Estado',
            color_discrete_map=color_map
        )
        st.plotly_chart(fig, width='stretch')

        st.subheader("Detalle de capacitaciones")

        # Tabla con colores por estado
        def color_estado(val):
            if val == "Vencido":
                return "background-color: #ffebee; color: #c62828; font-weight: bold;"
            elif val == "Próximo a vencer":
                return "background-color: #fff3e0; color: #e65100; font-weight: bold;"
            elif val == "Vigente":
                return "background-color: #e8f5e9; color: #2e7d32;"
            elif val == "Sin vencimiento":
                return "background-color: #e3f2fd; color: #1565c0;"
            return ""

        styled_df = asignaciones[['curso', 'cliente', 'fecha_asignacion_mostrar', 'fecha_vencimiento_mostrar', 'estado_mostrar', 'url_curso']]            .style            .map(color_estado, subset=['estado_mostrar'])

        st.dataframe(
            styled_df,
            width='stretch',
            hide_index=True,
            column_config={
                "fecha_asignacion_mostrar": "Fecha asignación",
                "fecha_vencimiento_mostrar": "Fecha vencimiento",
                "estado_mostrar": "Vigencia",
                "estado_bd_mostrar": "Ejecución",
                "url_curso": st.column_config.LinkColumn(
                    "Acceder al curso",
                    display_text="🔗 Abrir curso"
                )
            }
        )

    else:
        st.info("No tienes capacitaciones asignadas aún.")