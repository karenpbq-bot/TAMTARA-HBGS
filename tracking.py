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

    # --- FILA 1: SELECTOR DE VISTAS (Ancho libre para evitar cortes) ---
    navegacion = st.radio(
        "Seleccione Vista:",
        ["🔥 Pedidos en Proceso", "🗄️ Pedidos Cerrados", "📈 Informe de Ventas"], 
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
        # FILTRO ACTUALIZADO: Ignoramos la memoria temporal y leemos directamente la base de datos
        pedidos_tablero = [p for p in pedidos_filtrados if p.get('estado') != 'Cerrado']
        
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
                    cx1, cx2, cx3 = st.columns([0.60, 0.20, 0.20])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("👁️", key=f"pop_coc_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with cx3:
                        if st.button(">", key=f"fwd_coc_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.55, 0.15, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("<", key=f"rev_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("👁️", key=f"pop_bar_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        siguiente = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button(">", key=f"fwd_bar_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": siguiente}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO
        with col3:
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.55, 0.15, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("<", key=f"rev_cam_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("👁️", key=f"pop_cam_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        if st.button(">", key=f"fwd_cam_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()

        # 4. COLUMNA: ENTREGADO
        with col4:
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.55, 0.15, 0.15, 0.15])
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span></p>', unsafe_allow_html=True)
                    with cx2:
                        anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                        if st.button("<", key=f"rev_ent_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("👁️", key=f"pop_ent_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        # ACTUALIZACIÓN EN BASE DE DATOS PARA QUE EL ESTADO SEA PERMANENTE
                        if st.button(">", key=f"arc_ent_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Cerrado"}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # CASO 2: PEDIDOS CERRADOS CON HISTORIAL (MICRO-COMPACTO)
    # ==========================================
    elif navegacion == "🗄️ Pedidos Cerrados":
        # FILTRO ACTUALIZADO: Leemos el estado 'Cerrado' directo de Supabase
        archivados_del_turno = [p for p in todos_los_pedidos if p.get('estado') == 'Cerrado']
        
        # --- SISTEMA DE ALERTA Y PURGA EN UNA SOLA FILA ULTRA-COMPACTA ---
        total_registros_sistema = len(todos_los_pedidos)
        limite_preventivo = 10000
        
        # Grilla de 3 columnas para meter todo el control en un solo renglón
        c_inf1, c_inf2, c_inf3 = st.columns([0.25, 0.45, 0.30])
        
        with c_inf1:
            st.markdown(f"**BD:** {total_registros_sistema} / {limite_preventivo} ped.")
        
        with c_inf2:
            if total_registros_sistema >= limite_preventivo:
                st.markdown("⚠️ :orange[**Base de datos casi llena. Purgar.**]")
            else:
                st.markdown("🟢 :green[**Almacenamiento óptimo.**]")
        
        with c_inf3:
            if archivados_del_turno:
                if st.button("🗑️ Vaciar Historial", use_container_width=True, key="btn_purgar_micro", help="Borra definitivamente estos registros de Supabase"):
                    ids_a_borrar = [int(p['id']) for p in archivados_del_turno]
                    try:
                        db.table("pedidos").delete().in_("id", ids_a_borrar).execute()
                        st.success(f"Eliminados {len(ids_a_borrar)} pedidos.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.markdown("<div style='border-top: 1px dashed #cccccc; margin-top: 2px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        # --- DESPLIEGUE DE LISTA DE PEDIDOS ---
        if not archivados_del_turno:
            st.info("No se registran pedidos archivados.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([0.76, 0.12, 0.12])
                    with ch1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>🟢 N° {p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span> • Total: <b>S/. {p["monto_total"]:.2f}</b></p>', unsafe_allow_html=True)
                    with ch2:
                        if st.button("👁️", key=f"pop_hist_{p['id']}", use_container_width=True):
                            mostrar_ventana_emergente_detalle(p)
                    with ch3:
                        # ACTUALIZACIÓN: Cambiamos estado de vuelta a Entregado en Base de Datos
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True):
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()
    # ==========================================
    # CASO 3: INFORME DE VENTAS Y EXPORTACIÓN EXCEL
    # ==========================================
    elif navegacion == "📈 Informe de Ventas":
        st.markdown('<p class="titulo-carril" style="text-align:left; padding-left:15px; font-size:1rem !important;">📈 Panel de Análisis Financiero y Exportación</p>', unsafe_allow_html=True)
        
        with st.container(border=True):
            # 1. Filtro de Rango de Fechas
            c_f1, c_f2, _ = st.columns([1, 1, 2])
            fecha_inicio = c_f1.date_input("Fecha de Inicio:", value=datetime.now().date(), format="DD/MM/YYYY")
            fecha_fin = c_f2.date_input("Fecha de Fin:", value=datetime.now().date(), format="DD/MM/YYYY")

            # 2. Lógica de Filtrado por Fecha y Estado (Solo Entregados / Cobrados)
            pedidos_rango = []
            for p in todos_los_pedidos:
                # Nos aseguramos de contar solo lo que realmente se vendió (Entregado)
                if p.get('estado') == 'Entregado':
                    fecha_str = str(p.get('created_at', ''))
                    if len(fecha_str) >= 10:
                        try:
                            # Extraemos solo el YYYY-MM-DD de Supabase (ej: 2026-07-28)
                            fecha_pedido = datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
                            if fecha_inicio <= fecha_pedido <= fecha_fin:
                                pedidos_rango.append(p)
                        except:
                            continue

            # 3. Cálculo de KPIs Financieros
            if pedidos_rango:
                total_ingresos = sum(float(p.get('monto_total', 0)) for p in pedidos_rango)
                total_pedidos_rango = len(pedidos_rango)
                ticket_promedio = total_ingresos / total_pedidos_rango if total_pedidos_rango > 0 else 0
                
                # Desglose por Método de Pago
                ingresos_efectivo = sum(float(p['monto_total']) for p in pedidos_rango if p.get('metodo_pago') == 'Efectivo')
                ingresos_yape = sum(float(p['monto_total']) for p in pedidos_rango if p.get('metodo_pago') == 'Yape / Plin')
                ingresos_tarjeta = sum(float(p['monto_total']) for p in pedidos_rango if p.get('metodo_pago') == 'Tarjeta')

                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Total Ingresos", f"S/. {total_ingresos:.2f}")
                m2.metric("📦 Cantidad de Pedidos", f"{total_pedidos_rango}")
                m3.metric("🧾 Ticket Promedio", f"S/. {ticket_promedio:.2f}")
                m4.metric("💳 Yape/Plin + Tarjeta", f"S/. {(ingresos_yape + ingresos_tarjeta):.2f}")
                
                st.caption(f"**Desglose:** Efectivo: S/. {ingresos_efectivo:.2f} | Yape/Plin: S/. {ingresos_yape:.2f} | Tarjeta: S/. {ingresos_tarjeta:.2f}")
                
                # 4. Preparación y Generación del Archivo Excel
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Aplanamos los datos para que sean legibles en Excel
                datos_excel = []
                for p in pedidos_rango:
                    fecha_limpia = p['created_at'][:10] if isinstance(p.get('created_at'), str) else ""
                    hora_limpia = p['created_at'][11:19] if isinstance(p.get('created_at'), str) and len(p['created_at']) > 15 else ""
                    
                    # Extraer un resumen rápido de los items consumidos
                    resumen_items = " | ".join([f"{item['cantidad']}x {item['nombre']}" for item in p.get('items', [])])
                    
                    datos_excel.append({
                        "ID Base Datos": p['id'],
                        "Código Pedido": p['codigo_exacta'],
                        "Fecha": fecha_limpia,
                        "Hora": hora_limpia,
                        "Cliente": p.get('cliente', ''),
                        "Canal": p.get('tipo_entrega', ''),
                        "Monto Total (S/.)": float(p.get('monto_total', 0)),
                        "Método de Pago": p.get('metodo_pago', ''),
                        "N° Operación": p.get('num_operacion', ''),
                        "Resumen de Compra": resumen_items
                    })
                
                df_export = pd.DataFrame(datos_excel)
                
                # Proceso de exportación a BytesIO
                import io
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name="Ventas")
                
                # Botón de Descarga
                st.download_button(
                    label="📥 Descargar Informe Completo en Excel",
                    data=buffer_excel.getvalue(),
                    file_name=f"Informe_Ventas_La_Exacta_{fecha_inicio}_al_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            else:
                st.divider()
                st.info(f"No se registraron ventas en estado 'Entregado' para el rango del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}.")
                
