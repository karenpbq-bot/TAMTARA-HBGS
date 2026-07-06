import streamlit as st
import pandas as pd
from database import conectar
from datetime import datetime

def mostrar_modulo_tracking():
    # --- CONFIGURACIÓN DE PÁGINA ANCHA ---
    # Nota: Si ya llamas a st.set_page_config en tu main.py, es ideal asegurarse de que tenga layout="wide"
    try:
        st.set_page_config(layout="wide")
    except:
        # Si ya se configuró en el main, Streamlit ignorará esta línea sin lanzar error crítico
        pass

    # --- INYECCIÓN DE STYLES CSS PARA MÁXIMO ANCHO Y DENSIDAD ---
    st.markdown("""
        <style>
            /* Eliminar márgenes internos de Streamlit para aprovechar toda la pantalla */
            div.block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }
            
            /* Ajustar títulos de los carriles */
            .titulo-carril {
                font-size: 0.85rem !important;
                font-weight: bold !important;
                margin: 0 !important;
                padding: 4px 0 !important;
                text-align: center;
                background-color: #f1f3f5 !important;
                border-radius: 4px !important;
                border: 1px solid #e9ecef !important;
            }
            
            /* Línea divisoria horizontal */
            .linea-division {
                border-top: 2px solid #343a40 !important;
                margin-top: 2px !important;
                margin-bottom: 6px !important;
            }
            
            /* Rectángulos de pedidos expandidos a lo ancho */
            div[data-testid="stBlock"] div[data-testid="element-container"] .stContainer {
                padding: 2px 6px !important;
                margin-bottom: 2px !important;
                border-radius: 3px !important;
                background-color: #fdfdfd !important;
                border: 1px solid #dcdcdc !important;
                width: 100% !important; /* Fuerza el uso del 100% del carril */
            }
            
            /* Texto en una sola línea continua */
            div[data-testid="stBlock"] div[data-testid="element-container"] p {
                font-size: 0.72rem !important; /* Incrementado sutilmente para mejor lectura aprovechando el ancho */
                margin: 0 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                line-height: 22px !important; 
            }
            
            /* Forzar comportamiento alineado en la grilla interna de las tarjetas */
            div[data-testid="stHorizontalBlock"] {
                gap: 2px !important;
                align-items: center !important;
            }
            
            .titulo-tablero {
                font-size: 1.20rem !important;
                font-weight: bold !important;
                margin: 0 !important;
                padding: 0 !important;
                line-height: 35px !important;
            }
            
            div[data-testid="stTabs"] {
                margin-top: -10px !important;
            }
            
            /* =======================================================
               🔥 SELECCIÓN ABSOLUTA POR POSICIÓN DE COLUMNA DE BOTÓN
               ======================================================= */
            /* Botón Avanzar (VERDE) */
            div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
                background-color: #28a745 !important;
                color: white !important;
                border: 1px solid #28a745 !important;
                font-weight: bold !important;
                font-size: 0.80rem !important;
                height: 22px !important;
                min-height: 22px !important;
                line-height: 1 !important;
                padding: 0px !important;
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
                background-color: #218838 !important;
            }

            /* Botón Regresar (AZUL) */
            div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
                background-color: #007bff !important;
                color: white !important;
                border: 1px solid #007bff !important;
                font-weight: bold !important;
                font-size: 0.80rem !important;
                height: 22px !important;
                min-height: 22px !important;
                line-height: 1 !important;
                padding: 0px !important;
            }
            div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:hover {
                background-color: #0069d9 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    db = conectar()
    
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

    # --- CABECERA COMPACTA ---
    c_header1, c_header2 = st.columns([0.3, 0.7])
    with c_header1:
        st.markdown('<p class="titulo-tablero">📋 Tablero de Pedidos</p>', unsafe_allow_html=True)
    with c_header2:
        busqueda = st.text_input("", placeholder="🔍 Filtrar por código, cliente o mesa...", label_visibility="collapsed").strip().lower()

    if busqueda:
        pedidos_filtrados = []
        for p in todos_los_pedidos:
            cadena_auditoria = f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
            if busqueda in cadena_auditoria:
                pedidos_filtrados.append(p)
    else:
        pedidos_filtrados = todos_los_pedidos

    tab_proceso, tab_historial = st.tabs(["🔥 Pedidos en Proceso (Tablero)", "🗄️ Historial de Archivados"])

    # ==========================================
    # PESTAÑA 1: TABLERO KANBAN DE 4 COLUMNAS
    # ==========================================
    with tab_proceso:
        pedidos_tablero = [p for p in pedidos_filtrados if st.session_state.get(f"archivado_{p['id']}", False) != True]
        
        en_cocina = [p for p in pedidos_tablero if p.get('estado') == 'En cocina']
        listos = [p for p in pedidos_tablero if p.get('estado') == 'Listo']
        despachados = [p for p in pedidos_tablero if p.get('estado') == 'Despachado']
        entregados = [p for p in pedidos_tablero if p.get('estado') == 'Entregado']

        # Fila 1: Títulos de Carriles Alineados Estrictamente
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        with t_col1:
            st.markdown('<p class="titulo-carril">👨‍🍳 En Cocina</p>', unsafe_allow_html=True)
            st.markdown('<div class="linea-division"></div>', unsafe_allow_html=True)
        with t_col2:
            st.markdown('<p class="titulo-carril">🛎️ Listo en Barra</p>', unsafe_allow_html=True)
            st.markdown('<div class="linea-division"></div>', unsafe_allow_html=True)
        with t_col3:
            st.markdown('<p class="titulo-carril">🛵 En Camino</p>', unsafe_allow_html=True)
            st.markdown('<div class="linea-division"></div>', unsafe_allow_html=True)
        with t_col4:
            st.markdown('<p class="titulo-carril">🏁 Entregado</p>', unsafe_allow_html=True)
            st.markdown('<div class="linea-division"></div>', unsafe_allow_html=True)

        # Fila 2: Renderizado de Tarjetas Planas sobre Columnas Expandidas
        col1, col2, col3, col4 = st.columns(4)

        # 1. COLUMNA: EN COCINA
        with col1:
            for p in en_cocina:
                with st.container(border=True):
                    cx1, cx2 = st.columns([0.82, 0.18])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button(">", key=f"fwd_coc_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.76, 0.12, 0.12])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        siguiente_estado = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button(">", key=f"fwd_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": siguiente_estado}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO
        with col3:
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.76, 0.12, 0.12])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button(">", key=f"fwd_cam_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_cam_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 4. COLUMNA: ENTREGADO
        with col4:
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.76, 0.12, 0.12])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button(">", key=f"arc_ent_{p['id']}", use_container_width=True, help="Archivar permanentemente"):
                            st.session_state[f"archivado_{p['id']}"] = True
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_ent_{p['id']}", use_container_width=True):
                            anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # PESTAÑA 2: HISTORIAL DE ARCHIVADOS
    # ==========================================
    with tab_historial:
        st.subheader("📋 Historial de Órdenes Archivadas")
        
        archivados_del_turno = [p for p in pedidos_filtrados if p.get('estado') == 'Entregado' and st.session_state.get(f"archivado_{p['id']}", False)]
        
        if not archivados_del_turno:
            st.info("No hay pedidos archivados de forma definitiva en esta sesión todavía.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2 = st.columns([0.90, 0.10])
                    with ch1:
                        st.markdown(f"**🟢 N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})` • Total: S/. {p['monto_total']:.2f}")
                    with ch2:
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True, help="Regresar al Tablero"):
                            st.session_state[f"archivado_{p['id']}"] = False
                            st.rerun()
