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
            .texto-pedido-compacto {
                font-size: 0.78rem !important;
                margin: 0 !important;
                line-height: 1.2 !important;
                color: #313131 !important;
            }
            .parentesis-verde {
                color: #28a745 !important;
                font-weight: bold !important;
            }
        </style>
    """, unsafe_allow_html=True)

    db = conectar()
    
    # --- CONSULTA REAL SIN CACHÉ (PEDIDOS EN TIEMPO REAL) ---
    try:
        res = db.table("pedidos").select("*").order("id").execute()
        todos_los_pedidos = res.data if res.data else []
        
        prefijo_hoy = datetime.now().strftime("%d%m")
        for p in todos_los_pedidos:
            p['codigo_exacta'] = f"{prefijo_hoy}-{int(p['id']):03d}"
            
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return

    if not todos_los_pedidos:
        st.info("No hay registros de pedidos en el sistema actualmente.")
        return

    # --- FILA 1: SELECTOR DE VISTAS (Aislado a la izquierda) ---
    c_pestana, _ = st.columns([0.4, 0.6])
    with c_pestana:
        navegacion = st.radio(
            "Seleccione Vista:",
            ["🔥 Pedidos en Proceso", "🗄️ Pedidos Cerrados"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
    # --- FILA 2: FILTRO UNIVERSAL (Abarca el 100% del ancho del tablero) ---
    busqueda = st.text_input(
        "", 
        placeholder="🔍 Filtrar inmediatamente por código, cliente o mesa...", 
        label_visibility="collapsed"
    ).strip().lower()

    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # Filtrado lógico inmediato
    if busqueda:
        pedidos_filtrados = [
            p for p in todos_los_pedidos 
            if busqueda in f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
        ]
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
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button(">", key=f"fwd_coc_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        siguiente = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button(">", key=f"fwd_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": siguiente}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("<", key=f"rev_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO
        with col3:
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
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
                    cx1, cx2, cx3 = st.columns([0.70, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
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
        
        # Obtener los pedidos que están en estado 'Entregado' y marcados como archivados en la sesión
        archivados_del_turno = [p for p in todos_los_pedidos if p.get('estado') == 'Entregado' and st.session_state.get(f"archivado_{p['id']}", False)]
        
        # --- SISTEMA DE ALERTA DE CAPACIDAD DE BASE DE DATOS ---
        total_registros_sistema = len(todos_los_pedidos)
        limite_preventivo = 10000  # Alerta a los 10k registros para mantener la velocidad óptima
        
        c_info1, c_info2 = st.columns([0.5, 0.5])
        with c_info1:
            st.metric("Pedidos Totales en BD", f"{total_registros_sistema} / {limite_preventivo}")
        
        with c_info2:
            if total_registros_sistema >= limite_preventivo:
                st.warning("⚠️ ALERTA: La base de datos está acumulando demasiados registros. Se recomienda vaciar el historial para evitar lentitud.")
            else:
                st.success("🟢 Almacenamiento optimizado. Espacio en base de datos al 100% disponible.")
        
        st.divider()
        
        # --- BOTÓN DE BORRADO PERMANENTE ---
        if not archivados_del_turno:
            st.info("No se registran pedidos archivados en esta sesión.")
        else:
            # Botón de peligro para purgar la base de datos
            if st.button("🗑️ Vaciar Historial Permanentemente", use_container_width=True, type="secondary", help="Borra definitivamente estos registros de Supabase"):
                ids_a_borrar = [int(p['id']) for p in archivados_del_turno]
                
                try:
                    with st.spinner("Purgando registros de Supabase..."):
                        # Borrar físicamente de la tabla pedidos en la base de datos
                        db.table("pedidos").delete().in_("id", ids_a_borrar).execute()
                        
                        # Limpiar los estados de archivado en la sesión para esos IDs
                        for pid in ids_a_borrar:
                            if f"archivado_{pid}" in st.session_state:
                                del st.session_state[f"archivado_{pid}"]
                                
                    st.success(f"💥 Éxito: Se eliminaron {len(ids_a_borrar)} pedidos cerrados de la base de datos.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al intentar purgar la base de datos: {e}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Desplegar la lista de pedidos archivados por si se necesita revisar antes de borrar
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([0.70, 0.15, 0.15])
                    with ch1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>🟢 N° {p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span> • Total: <b>S/. {p["monto_total"]:.2f}</b></p>', unsafe_allow_html=True)
                    with ch2:
                        if st.button("👁️", key=f"pop_hist_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with ch3:
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True):
                            st.session_state[f"archivado_{p['id']}"] = False
                            st.rerun()
