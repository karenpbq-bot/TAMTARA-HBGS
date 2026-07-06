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
    # --- CSS MÍNIMO SÓLO PARA ESTRUCTURA ANCHA ---
    st.markdown("""
        <style>
            div.block-container {
                padding-top: 2rem !important; 
                padding-bottom: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }
            .titulo-carril {
                font-size: 0.85rem !important;
                font-weight: bold !important;
                margin: 0 !important;
                padding: 6px 0 !important;
                text-align: center;
                background-color: #f1f3f5 !important;
                border-radius: 4px !important;
                border: 1px solid #e9ecef !important;
            }
            .linea-division {
                border-top: 2px solid #343a40 !important;
                margin-top: 2px !important;
                margin-bottom: 6px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    db = conectar()
    
    # --- CARGA OPTIMIZADA EN MEMORIA VIVA ---
    if 'lista_pedidos_tracking' not in st.session_state:
        try:
            res = db.table("pedidos").select("*").order("id").execute()
            todos_los_pedidos = res.data if res.data else []
            
            for p in todos_los_pedidos:
                try:
                    dt = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
                    prefijo_fecha = dt.strftime("%d%m")
                except:
                    prefijo_fecha = datetime.now().strftime("%d%m")
                p['codigo_exacta'] = f"{prefijo_fecha}-{int(p['id']):03d}"
                
            st.session_state.lista_pedidos_tracking = todos_los_pedidos
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            return

    pedidos_actuales = st.session_state.lista_pedidos_tracking

    if not pedidos_actuales:
        st.info("No hay registros de pedidos en el sistema.")
        return

    # --- CABECERA INTEGRADA HORIZONTAL CORREGIDA (Distribución 0.3 a 0.7 para expandir el filtro) ---
    c_nav1, c_nav2 = st.columns([0.3, 0.7])
    
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
        pedidos_filtrados = [
            p for p in pedidos_actuales 
            if busqueda in f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
        ]
    else:
        pedidos_filtrados = pedidos_actuales

    # ==========================================
    # CASO 1: TABLERO KANBAN DE 4 COLUMNAS
    # ==========================================
    if navegacion == "🔥 Pedidos en Proceso":
        pedidos_tablero = [p for p in pedidos_filtrados if st.session_state.get(f"archivado_{p['id']}", False) != True]
        
        en_cocina = [p for p in pedidos_tablero if p.get('estado') == 'En cocina']
        listos = [p for p in pedidos_tablero if p.get('estado') == 'Listo']
        despachados = [p for p in pedidos_tablero if p.get('estado') == 'Despachado']
        entregados = [p for p in pedidos_tablero if p.get('estado') == 'Entregado']

        # Títulos de Carriles
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

        # 1. COLUMNA: EN COCINA
        with col1:
            for p in en_cocina:
                with st.container(border=True):
                    cx1, cx2 = st.columns([0.80, 0.20])
                    with cx1:
                        # Se aplica el formato de texto pequeño (.caption) para encoger la tipografía
                        st.caption(f"**{p['codigo_exacta']}** {p['cliente']} :green[({p['destino_entrega']})]")
                    with cx2:
                        if st.button(">", key=f"fwd_coc_{p['id']}", use_container_width=True):
                            p['estado'] = "Listo"
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.caption(f"**{p['codigo_exacta']}** {p['cliente']} :green[({p['destino_entrega']})]")
                    with cx2:
                        siguiente = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button(">", key=f"fwd_bar_{p['id']}", use_container_width=True):
                            p['estado'] = penultimate_status_check if siguiente == "Despachado" else "Entregado"
                            p['estado'] = siguiente
                            db.table("pedidos").update({"estado": siguiente}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_bar_{p['id']}", use_container_width=True):
                            p['estado'] = "En cocina"
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO
        with col3:
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.caption(f"**{p['codigo_exacta']}** {p['cliente']} :green[({p['destino_entrega']})]")
                    with cx2:
                        if st.button(">", key=f"fwd_cam_{p['id']}", use_container_width=True):
                            p['estado'] = "Entregado"
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_cam_{p['id']}", use_container_width=True):
                            p['estado'] = "Listo"
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 4. COLUMNA: ENTREGADO
        with col4:
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.caption(f"**{p['codigo_exacta']}** {p['cliente']} :green[({p['destino_entrega']})]")
                    with cx2:
                        if st.button(">", key=f"arc_ent_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = True
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_ent_{p['id']}", use_container_width=True):
                            anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                            p['estado'] = anterior
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # CASO 2: PEDIDOS CERRADOS CON HISTORIAL
    # ==========================================
    elif navegacion == "🗄️ Pedidos Cerrados":
        st.markdown("### 🗄️ Historial de Órdenes Archivadas")
        
        archivados_del_turno = [p for p in pedidos_filtrados if p.get('estado') == 'Entregado' and st.session_state.get(f"archivado_{p['id']}", False)]
        
        if not archivados_del_turno:
            st.info("No se registran pedidos archivados en esta sesión.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([0.70, 0.15, 0.15])
                    with ch1:
                        st.caption(f"**🟢 N° {p['codigo_exacta']}** • {p['cliente']} :green[({p['destino_entrega']})] • Total: **S/. {p['monto_total']:.2f}**")
                    with ch2:
                        if st.button("👁️", key=f"pop_hist_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with ch3:
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = False
                            st.rerun()
