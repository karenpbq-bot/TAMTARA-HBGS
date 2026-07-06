import streamlit as st
import pandas as pd
from database import conectar
from datetime import datetime

def mostrar_modulo_tracking():
    # --- INYECCIÓN DE STYLES PARA MÁXIMA DENSIDAD VERTICAL (DISEÑO PLANO) ---
    st.markdown("""
        <style>
            /* 1. Ajustar los encabezados de las 4 columnas */
            .stHeading h3 {
                font-size: 0.95rem !important;
                margin: 0 !important;
                padding: 2px 0 !important;
                text-align: center;
            }
            /* 2. Convertir las tarjetas en filas ultra planas de 0 margen */
            div[data-testid="stBlock"] div[data-testid="element-container"] .stContainer {
                padding: 2px 4px !important;
                margin-bottom: 2px !important;
                border-radius: 3px !important;
                background-color: #fcfcfc !important;
                border: 1px solid #e0e0e0 !important;
            }
            /* 3. Forzar texto en tamaño micro y evitar saltos de línea */
            div[data-testid="stBlock"] div[data-testid="element-container"] p {
                font-size: 0.78rem !important;
                margin: 0 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            /* 4. Encoger los botones a tamaño miniatura */
            div[data-testid="stBlock"] button {
                padding: 1px 2px !important;
                font-size: 0.72rem !important;
                min-height: 20px !important;
                height: 22px !important;
                line-height: 1 !important;
            }
            /* Estilo para espaciado general de la grilla */
            [data-testid="stHorizontalBlock"] {
                gap: 4px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("📋 Tablero de Control de Producción - La Exacta")
    db = conectar()
    
    # Extraemos todos los registros de la base de datos
    try:
        res = db.table("pedidos").select("*").order("id").execute()
        todos_los_pedidos = res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return

    if not todos_los_pedidos:
        st.info("No hay registros de pedidos en el sistema.")
        return

    # --- LÓGICA DE FORMATEO: CÓDIGO DDMM-CORRELATIVO ---
    for p in todos_los_pedidos:
        try:
            dt = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
            prefijo_fecha = dt.strftime("%d%m")
        except:
            prefijo_fecha = datetime.now().strftime("%d%m")
        p['codigo_exacta'] = f"{prefijo_fecha}-{int(p['id']):03d}"

    # --- BARRA DE BÚSQUEDA UNIVERSAL ---
    busqueda = st.text_input("🔍 Filtrar pedido:", placeholder="Escribe código, cliente o mesa...").strip().lower()

    if busqueda:
        pedidos_filtrados = []
        for p in todos_los_pedidos:
            cadena_auditoria = f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
            if busqueda in cadena_auditoria:
                pedidos_filtrados.append(p)
    else:
        pedidos_filtrados = todos_los_pedidos

    # Separación por pestañas requeridas
    tab_proceso, tab_historial = st.tabs(["🔥 Pedidos en Proceso (Tablero)", "🗄️ Historial de Archivados"])

    # ==========================================
    # PESTAÑA 1: TABLERO KANBAN DE 4 COLUMNAS
    # ==========================================
    with tab_proceso:
        # Filtramos para mostrar los 4 estados activos antes del archivado permanente
        # Creamos una marca en el payload si el pedido ya fue mandado permanentemente al historial
        pedidos_tablero = [p for p in pedidos_filtrados if p.get('archivado_final') != True]
        
        # Separación estricta en los 4 estados funcionales
        en_cocina = [p for p in pedidos_tablero if p.get('estado') == 'En cocina']
        listos = [p for p in pedidos_tablero if p.get('estado') == 'Listo']
        despachados = [p for p in pedidos_tablero if p.get('estado') == 'Despachado']
        entregados = [p for p in pedidos_tablero if p.get('estado') == 'Entregado']

        # Crear la grilla de 4 columnas iguales para aprovechar la pantalla ancha
        col1, col2, col3, col4 = st.columns(4)

        # 1. COLUMNA: EN COCINA
        with col1:
            st.subheader("👨‍🍳 En Cocina")
            st.divider()
            for p in en_cocina:
                with st.container(border=True):
                    cx1, cx2 = st.columns([0.80, 0.20])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button("➡️", key=f"fwd_coc_{p['id']}", use_container_width=True, type="primary", help="Pasar a Barra"):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            st.subheader("🛎️ Listo en Barra")
            st.divider()
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.64, 0.18, 0.18])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        # CORREGIDO: Definición limpia del estado y actualización directa sin encadenamientos rotos
                        siguiente_estado = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button("➡️", key=f"fwd_bar_{p['id']}", use_container_width=True, type="primary"):
                            db.table("pedidos").update({"estado": siguiente_estado}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("⏪", key=f"rev_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO (SOLO DELIVERY)
        with col3:
            st.subheader("🛵 En Camino")
            st.divider()
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.64, 0.18, 0.18])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button("➡️", key=f"fwd_cam_{p['id']}", use_container_width=True, type="primary"):
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("⏪", key=f"rev_cam_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 4. COLUMNA NUEVA: ENTREGADO (CONFIRMACIÓN EN TABLERO)
        with col4:
            st.subheader("🏁 Entregado")
            st.divider()
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.64, 0.18, 0.18])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        # Este botón simula el archivado definitivo para limpiar el tablero diario
                        if st.button("🗄️", key=f"arc_ent_{p['id']}", use_container_width=True, help="Archivar permanentemente"):
                            # Usamos un campo temporal en la sesión o una actualización lógica para sacarlo del tablero activo
                            st.session_state[f"archivado_{p['id']}"] = True
                            st.rerun()
                    with cx3:
                        # Permite regresar el pedido si se marcó entregado por error
                        if st.button("⏪", key=f"rev_ent_{p['id']}", use_container_width=True):
                            anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # PESTAÑA 2: HISTORIAL DE ARCHIVADOS GENERAL
    # ==========================================
    with tab_historial:
        st.subheader("📋 Historial de Órdenes Archivadas")
        
        # Filtramos aquellos que el counter decidió sacar de la pantalla activa mediante el botón del maletín/archivador
        archivados_del_turno = [p for p in pedidos_filtrados if p.get('estado') == 'Entregado' and st.session_state.get(f"archivado_{p['id']}", False)]
        
        if not archivados_del_turno:
            st.info("No hay pedidos archivados de forma definitiva en esta sesión todavía.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2 = st.columns([0.85, 0.15])
                    with ch1:
                        st.markdown(f"**🟢 N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})` • Total: S/. {p['monto_total']:.2f}")
                    with ch2:
                        # Permite sacar del archivo y regresar al carril "Entregado" del tablero si se requiere
                        if st.button("Reactivar", key=f"react_hist_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = False
                            st.rerun()
