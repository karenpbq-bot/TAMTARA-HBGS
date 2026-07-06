import streamlit as st
import pandas as pd
from database import conectar
from datetime import datetime

# --- VENTANA EMERGENTE PARA DETALLE DE RECLAMOS/AUDITORÍA ---
@st.dialog("📋 Detalle del Pedido Cerrado")
def mostrar_ventana_emergente_detalle(pedido):
    st.markdown(f"### 🪪 Pedido N° {pedido['codigo_exacta']}")
    st.markdown(f"**Cliente:** {pedido['cliente']} | **Entrega:** {pedido['tipo_entrega']} (`{pedido['destino_entrega']}`)")
    st.markdown(f"**Monto Cobrado:** S/. {pedido['monto_total']:.2f} | **Forma de Pago:** {pedido['metodo_pago']}")
    if pedido.get('num_operacion'):
        st.caption(f"Ref. Operación: {pedido['num_operacion']}")
    
    st.divider()
    st.markdown("**🍟 Productos Consumidos:**")
    
    for item in pedido.get('items', []):
        p_ad_item = sum(float(a['precio']) for a in item.get('adicionales', []))
        sub_total_item = (item['precio_base'] + p_ad_item) * item['cantidad']
        
        st.markdown(f"**{item['cantidad']}x  {item['nombre']}** — *S/. {sub_total_item:.2f}*")
        if item.get('adicionales'):
            ads = ", ".join([f"{a['nombre']} (+S/. {a['precio']:.2f})" for a in item['adicionales']])
            st.markdown(f"   └  _Adicionales: {ads}_")
    st.divider()

def mostrar_modulo_tracking():
    # --- INYECCIÓN DE ESTILOS CSS REVISADA Y BLINDADA ---
    st.markdown("""
        <style>
            /* 1. Configuración del contenedor general en modo ancho */
            div.block-container {
                padding-top: 55px !important; 
                padding-bottom: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }

            /* 2. Cabeceras de los 4 carriles Kanban */
            .titulo-carril {
                font-size: 0.85rem !important;
                font-weight: bold !important;
                margin: 0 !important;
                padding: 6px 0 !important;
                text-align: center;
                background-color: #f1f3f5 !important;
                border-radius: 4px !important;
                border: 1px solid #e9ecef !important;
                color: #333333 !important;
            }

            .linea-division {
                border-top: 2px solid #343a40 !important;
                margin-top: 2px !important;
                margin-bottom: 6px !important;
            }

            /* 3. Rectángulos de los pedidos planos con tipografía micro */
            div[data-testid="stBlock"] div[data-testid="element-container"] .stContainer {
                padding: 3px 6px !important;
                margin-bottom: 3px !important;
                border-radius: 4px !important;
                background-color: #fdfdfd !important;
                border: 1px solid #cccccc !important;
                width: 100% !important;
            }

            /* Letras micro-compactas dentro del recuadro */
            div[data-testid="stBlock"] div[data-testid="element-container"] p {
                font-size: 0.75rem !important;
                margin: 0 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                line-height: 24px !important;
                color: #222222 !important;
            }

            /* 4. ALINEACIÓN CORREGIDA (Estilo base original sin forzar el techo vertical) */
            div.stContainer div[data-testid="stHorizontalBlock"] {
                gap: 4px !important;
                align-items: baseline !important;
            }

            /* =======================================================
               🎨 INYECCIÓN TOTAL DE COLOR A BOTONES NATIVOS
               ======================================================= */
            
            /* ---- BOTONES DE AVANCE, ARCHIVADO Y DETALLE (VERDE) ---- */
            div.stButton > button[key*="fwd_"], 
            div.stButton > button[key*="arc_"], 
            div.stButton > button[key*="pop_"] {
                background-color: #28a745 !important;
                border: 1px solid #28a745 !important;
                border-radius: 4px !important;
                height: 24px !important;
                padding: 0px 8px !important;
                min-height: 24px !important;
            }
            
            /* Forzar texto interno en blanco y negrita para botones verdes */
            div.stButton > button[key*="fwd_"] p,
            div.stButton > button[key*="arc_"] p,
            div.stButton > button[key*="pop_"] p {
                color: #ffffff !important;
                font-size: 0.85rem !important;
                font-weight: bold !important;
                line-height: 24px !important;
            }

            /* ---- BOTONES DE RETROCESO (AZUL) ---- */
            div.stButton > button[key*="rev_"] {
                background-color: #007bff !important;
                border: 1px solid #007bff !important;
                border-radius: 4px !important;
                height: 24px !important;
                padding: 0px 8px !important;
                min-height: 24px !important;
            }
            
            /* Forzar texto interno en blanco y negrita para botones azules */
            div.stButton > button[key*="rev_"] p {
                color: #ffffff !important;
                font-size: 0.85rem !important;
                font-weight: bold !important;
                line-height: 24px !important;
            }

            /* Ajuste de hovers para mantener consistencia visual */
            div.stButton > button[key*="fwd_"]:hover { background-color: #218838 !important; }
            div.stButton > button[key*="rev_"]:hover { background-color: #0069d9 !important; }
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

    # --- CABECERA INTEGRADA ---
    c_nav1, c_nav2 = st.columns([0.4, 0.6])
    
    with c_nav1:
        navegacion = st.radio(
            "Seleccione Vista:",
            ["🔥 Pedidos en Proceso", "🗄️ Pedidos Cerrados"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
    with c_nav2:
        busqueda = st.text_input(
            "", 
            placeholder="🔍 Filtrar inmediatamente por código, cliente o mesa...", 
            label_visibility="collapsed"
        ).strip().lower()

    if busqueda:
        pedidos_filtrados = []
        for p in todos_los_pedidos:
            cadena_auditoria = f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
            if busqueda in cadena_auditoria:
                pedidos_filtrados.append(p)
    else:
        pedidos_filtrados = todos_los_pedidos

    # ==========================================
    # CASO 1: TABLERO KANBAN DE 4 COLUMNAS
    # ==========================================
    if navegacion == "🔥 Pedidos en Proceso":
        pedidos_tablero = [p for p in pedidos_filtrados if st.session_state.get(f"archivado_{p['id']}", False) != True]
        
        en_cocina = [p for p in pedidos_tablero if p.get('estado') == 'En cocina']
        listos = [p for p in pedidos_tablero if p.get('estado') == 'Listo']
        despachados = [p for p in pedidos_tablero if p.get('estado') == 'Despachado']
        entregados = [p for p in pedidos_tablero if p.get('estado') == 'Entregado']

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

        col1, col2, col3, col4 = st.columns(4)

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

        with col4:
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.76, 0.12, 0.12])
                    with cx1:
                        st.markdown(f"**{p['codigo_exacta']}** {p['cliente']} `({p['destino_entrega']})`")
                    with cx2:
                        if st.button(">", key=f"arc_ent_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = True
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_ent_{p['id']}", use_container_width=True):
                            anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # CASO 2: PEDIDOS CERRADOS CON HISTORIAL
    # ==========================================
    elif navegacion == "🗄️ Pedidos Cerrados":
        st.markdown("### 🗄️ Historial de Órdenes Archivadas")
        
        archivados_del_turno = [p for p in todos_los_pedidos if p.get('estado') == 'Entregado' and st.session_state.get(f"archivado_{p['id']}", False)]
        
        if not archivados_del_turno:
            st.info("No se registran pedidos archivados de forma definitiva en el turno actual.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([0.76, 0.12, 0.12])
                    with ch1:
                        st.markdown(f"**🟢 N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})` • Total: **S/. {p['monto_total']:.2f}**")
                    with ch2:
                        if st.button("👁️", key=f"pop_hist_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with ch3:
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = False
                            st.rerun()
