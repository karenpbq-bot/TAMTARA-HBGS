import streamlit as st
import pandas as pd
import io
from database import conectar
from datetime import datetime, date, timedelta, timezone

# Declaramos la zona horaria fija de Perú (UTC-5)
ZONA_PERU = timezone(timedelta(hours=-5))

@st.dialog("📋 Detalle del Pedido")
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
            st.markdown(f"    └  _Adicionales: {ads}_")
    st.divider()

def mostrar_modulo_tracking():
    # --- CSS AVANZADO: MEJORA DE VISIBILIDAD EN PESTAÑAS Y BOTONES ---
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
                line-height: 1.25 !important;
                color: #313131 !important;
            }
            .parentesis-verde {
                color: #28a745 !important;
                font-weight: bold !important;
            }
            [data-testid="stButton"] {
                width: 100% !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
        </style>
    """, unsafe_allow_html=True)

    db = conectar()
    
    try:
        res = db.table("pedidos").select("*").order("id").execute()
        todos_los_pedidos = res.data if res.data else []
        
        for p in todos_los_pedidos:
            created_at_str = p.get('created_at')
            if created_at_str:
                try:
                    # Capturamos el formato UTC de Supabase y lo forzamos a hora Perú
                    dt_utc = datetime.strptime(created_at_str[:19], "%Y-%m-%dT%H:%M:%S")
                    dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                    dt_peru = dt_utc.astimezone(ZONA_PERU)
                    prefijo_fecha = dt_peru.strftime("%d%m")
                except:
                    prefijo_fecha = datetime.now(ZONA_PERU).strftime("%d%m")
            else:
                prefijo_fecha = datetime.now(ZONA_PERU).strftime("%d%m")
                
            p['codigo_exacta'] = f"{prefijo_fecha}-{int(p['id']):03d}"
            
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return

    # --- ENCABEZADO: SELECTOR DE VISTAS Y BOTÓN DE ACTUALIZACIÓN VISIBLES ---
    c_head1, c_head2 = st.columns([0.75, 0.25])
    with c_head1:
        navegacion = st.radio(
            ":",
            ["🔥 Pedidos en Proceso", "🗄️ Pedidos Cerrados", "📈 Informe de Ventas"], 
            horizontal=True
        )
    with c_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True, help="Refresca el tablero en tiempo real", type="secondary"):
            st.rerun()
        
    # --- FILA 2: FILTRO UNIVERSAL (SOLO PARA KANBAN / CERRADOS) ---
    if navegacion != "📈 Informe de Ventas":
        busqueda = st.text_input(
            "", 
            placeholder="🔍 Filtrar inmediatamente por código, cliente o mesa...", 
            label_visibility="collapsed"
        ).strip().lower()

        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        if busqueda:
            pedidos_filtrados = [
                p for p in todos_los_pedidos 
                if busqueda in f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')}".lower()
            ]
        else:
            pedidos_filtrados = todos_los_pedidos
    else:
        pedidos_filtrados = todos_los_pedidos

    # ==========================================
    # CASO 1: TABLERO KANBAN DE 4 COLUMNAS
    # ==========================================
    if navegacion == "🔥 Pedidos en Proceso":
        pedidos_tablero = [p for p in pedidos_filtrados if p.get('pedido_cerrado') != 'Sí']
        
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

        def obtener_resumen_jerarquizado(p):
            principales = []
            bebidas = []
            for item in p.get('items', []):
                p_code = item.get('codigo', '').strip()
                if not p_code:
                    p_code = item['nombre'][:3].upper()
                
                nombre_inf = item['nombre'].lower()
                if any(b in nombre_inf for b in ['cola', 'fanta', 'sprite', 'agua', 'energina', 'chicha', 'inka', 'bebida', 'jugo', 'cerveza', 'limonada']):
                    bebidas.append(p_code)
                else:
                    principales.append(p_code)
            
            ordenados = principales + bebidas
            return ", ".join(ordenados)

        # 1. COLUMNA: EN COCINA
        with col1:
            for p in en_cocina:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.64, 0.12, 0.12, 0.12])
                    detalle_str = obtener_resumen_jerarquizado(p)
                    
                    # Etiqueta visual sutil [P] en rojo si está pendiente de pago
                    tag_pendiente = ' <span style="color: #d9534f; font-weight: bold;">[P]</span>' if p.get('estado_pago') == 'Pendiente' else ''
                    detalle_html = f'<br><small style="color: #666;">📝 {detalle_str}</small>{tag_pendiente}' if (detalle_str or tag_pendiente) else ''
                    
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span>{detalle_html}</p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("📄", key=f"pop_coc_{p['id']}", use_container_width=True, help="Ver detalle"):
                            mostrar_ventana_emergente_detalle(p)
                    with cx3:
                        # SI ESTÁ PENDIENTE DE PAGO, REDIRIGE AL MENÚ (PASO 1) PARA AGREGAR PRODUCTOS
                        if p.get('estado_pago') == 'Pendiente':
                            if st.button("💳", key=f"cobrar_kanban_{p['id']}", use_container_width=True, help="Agregar más productos o cobrar"):
                                st.session_state['carrito'] = p.get('items', [])
                                st.session_state['cliente_actual'] = p.get('cliente', '')
                                st.session_state['paso_pedido'] = 1  # ⬅️ Cambio clave: Volvemos al catálogo
                                st.session_state['pedido_en_edicion_id'] = p['id']
                                
                                st.session_state['menu_activo_forzado'] = "Pedidos (Ventas)"
                                st.rerun()
                        else:
                            if st.button("🗑️", key=f"del_coc_{p['id']}", use_container_width=True, help="Eliminar pedido"):
                                db.table("pedidos").delete().eq("id", p['id']).execute()
                                st.rerun()
                    with cx4:
                        if st.button(">", key=f"fwd_coc_{p['id']}", use_container_width=True, help="Avanzar"):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

        # 2. COLUMNA: LISTO EN BARRA
        with col2:
            for p in listos:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.64, 0.12, 0.12, 0.12])
                    detalle_str = obtener_resumen_jerarquizado(p)
                    detalle_html = f'<br><small style="color: #666;">📝 {detalle_str}</small>' if detalle_str else ''
                    
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span>{detalle_html}</p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("<", key=f"rev_bar_{p['id']}", use_container_width=True, help="Retroceder"):
                            db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("📄", key=f"pop_bar_{p['id']}", use_container_width=True, help="Ver detalle"):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        siguiente = "Despachado" if p['tipo_entrega'] == "Delivery" else "Entregado"
                        if st.button(">", key=f"fwd_bar_{p['id']}", use_container_width=True, help="Avanzar"):
                            db.table("pedidos").update({"estado": siguiente}).eq("id", p['id']).execute()
                            st.rerun()

        # 3. COLUMNA: EN CAMINO
        with col3:
            for p in despachados:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.64, 0.12, 0.12, 0.12])
                    detalle_str = obtener_resumen_jerarquizado(p)
                    detalle_html = f'<br><small style="color: #666;">📝 {detalle_str}</small>' if detalle_str else ''
                    
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span>{detalle_html}</p>', unsafe_allow_html=True)
                    with cx2:
                        if st.button("<", key=f"rev_cam_{p['id']}", use_container_width=True, help="Retroceder"):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("📄", key=f"pop_cam_{p['id']}", use_container_width=True, help="Ver detalle"):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        if st.button(">", key=f"fwd_cam_{p['id']}", use_container_width=True, help="Avanzar"):
                            db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                            st.rerun()

        # 4. COLUMNA: ENTREGADO
        with col4:
            for p in entregados:
                with st.container(border=True):
                    cx1, cx2, cx3, cx4 = st.columns([0.64, 0.12, 0.12, 0.12])
                    detalle_str = obtener_resumen_jerarquizado(p)
                    detalle_html = f'<br><small style="color: #666;">📝 {detalle_str}</small>' if detalle_str else ''
                    
                    with cx1:
                        st.markdown(f'<p class="texto-pedido-compacto"><b>{p["codigo_exacta"]}</b> • {p["cliente"]} <span class="parentesis-verde">({p["destino_entrega"]})</span>{detalle_html}</p>', unsafe_allow_html=True)
                    with cx2:
                        anterior = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                        if st.button("<", key=f"rev_ent_{p['id']}", use_container_width=True, help="Retroceder"):
                            db.table("pedidos").update({"estado": anterior}).eq("id", p['id']).execute()
                            st.rerun()
                    with cx3:
                        if st.button("📄", key=f"pop_ent_{p['id']}", use_container_width=True, help="Ver detalle"):
                            mostrar_ventana_emergente_detalle(p)
                    with cx4:
                        if st.button(">", key=f"arc_ent_{p['id']}", use_container_width=True, help="Archivar"):
                            db.table("pedidos").update({"pedido_cerrado": "Sí"}).eq("id", p['id']).execute()
                            st.rerun()

    # ==========================================
    # CASO 2: PEDIDOS CERRADOS CON HISTORIAL
    # ==========================================
    elif navegacion == "🗄️ Pedidos Cerrados":
        # Extraemos los cerrados y aplicamos slicing inverso [::-1] para mostrar los más recientes arriba
        archivados_del_turno = [p for p in todos_los_pedidos if p.get('pedido_cerrado') == 'Sí'][::-1]
        
        c_inf1, c_inf2, c_inf3 = st.columns([0.25, 0.45, 0.30])
        with c_inf1:
            st.markdown(f"**BD:** {len(todos_los_pedidos)} ped.")
        with c_inf2:
            st.markdown("🟢 :green[**Almacenamiento óptimo.**]")
        with c_inf3:
            if archivados_del_turno:
                if st.button("🗑️ Vaciar Todo el Historial", use_container_width=True, key="btn_purgar_micro"):
                    ids_a_borrar = [int(p['id']) for p in archivados_del_turno]
                    try:
                        db.table("pedidos").delete().in_("id", ids_a_borrar).execute()
                        st.rerun()
                    except Exception:
                        pass
        
        st.markdown("<div style='border-top: 1px dashed #cccccc; margin-top: 2px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        
        if not archivados_del_turno:
            st.info("No se registran pedidos cerrados.")
        else:
            for p in archivados_del_turno:
                with st.container(border=True):
                    ch1, ch2, ch3, ch4 = st.columns([0.64, 0.12, 0.12, 0.12])
                    with ch1:
                        tag_cortesia = " 🎁 [CORTESÍA]" if p.get('cortesia') == 'Sí' else ""
                        st.markdown(f'<p class="texto-pedido-compacto"><b>🟢 N° {p["codigo_exacta"]}</b> • {p["cliente"]}{tag_cortesia} <span class="parentesis-verde">({p["destino_entrega"]})</span> • Total: <b>S/. {p["monto_total"]:.2f}</b></p>', unsafe_allow_html=True)
                    with ch2:
                        if st.button("📄", key=f"pop_hist_{p['id']}", use_container_width=True, help="Ver detalle"):
                            mostrar_ventana_emergente_detalle(p)
                    with ch3:
                        if st.button("<", key=f"rev_hist_{p['id']}", use_container_width=True, help="Retroceder"):
                            db.table("pedidos").update({"pedido_cerrado": "No"}).eq("id", p['id']).execute()
                            st.rerun()
                    with ch4:
                        if st.button("🗑️", key=f"del_hist_{p['id']}", use_container_width=True, help="Eliminar"):
                            db.table("pedidos").delete().eq("id", p['id']).execute()
                            st.rerun()

    ## ==========================================
    # CASO 3: INFORME DE VENTAS Y ESTADÍSTICAS
    # ==========================================
    elif navegacion == "📈 Informe de Ventas":
        st.markdown('<p class="titulo-carril" style="text-align:left; padding-left:15px; font-size:1rem !important;">📈 Dashboard de Ventas y Estadísticas</p>', unsafe_allow_html=True)
        
        # --- 1. FILTROS GLOBALES (Fuera de los expanders) ---
        c_f1, c_f2, _ = st.columns([1, 1, 2])
        fecha_inicio = c_f1.date_input("Fecha de Inicio:", value=datetime.now(ZONA_PERU).date(), format="DD/MM/YYYY", key="inf_f_ini")
        fecha_fin = c_f2.date_input("Fecha de Fin:", value=datetime.now(ZONA_PERU).date(), format="DD/MM/YYYY", key="inf_f_fin")

        # FILTRADO ROBUSTO POR RANGO DE FECHAS (Traduciendo UTC a ZONA_PERU)
        pedidos_rango = []
        for p in todos_los_pedidos:
            created_str = p.get('created_at')
            if created_str:
                try:
                    dt_utc = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                    dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                    p_date = dt_utc.astimezone(ZONA_PERU).date()
                    
                    if fecha_inicio <= p_date <= fecha_fin:
                        pedidos_rango.append(p)
                except:
                    pass

        if pedidos_rango:
            # Excluimos cortesías y pedidos no pagados para el análisis financiero
            ingresos_validos = [p for p in pedidos_rango if p.get('cortesia') != 'Sí' and p.get('estado_pago') == 'Pagado']
            total_ingresos = sum(float(p.get('monto_total', 0)) for p in ingresos_validos)

            # --- PRE-PROCESAMIENTO DE PRODUCTOS VENDIDOS ---
            diccionario_ventas = {}
            for p in ingresos_validos:
                for item in p.get('items', []):
                    nombre_prod = item.get('nombre', 'Desconocido')
                    cant = int(item.get('cantidad', 0))
                    
                    # Identificación automática de categoría (Heurística)
                    nombre_inf = nombre_prod.lower()
                    if any(b in nombre_inf for b in ['cola', 'fanta', 'sprite', 'agua', 'energina', 'chicha', 'inka', 'bebida', 'jugo', 'cerveza', 'limonada']):
                        categoria = 'Bebidas'
                    else:
                        categoria = 'Principales'
                    
                    # Cálculo del subtotal incluyendo adicionales
                    p_ad = sum(float(a.get('precio', 0)) for a in item.get('adicionales', []))
                    subtotal = (float(item.get('precio_base', 0)) + p_ad) * cant
                    
                    if nombre_prod not in diccionario_ventas:
                        diccionario_ventas[nombre_prod] = {"Cantidad": 0, "Monto Total (S/.)": 0.0, "Categoría": categoria}
                    
                    diccionario_ventas[nombre_prod]["Cantidad"] += cant
                    diccionario_ventas[nombre_prod]["Monto Total (S/.)"] += subtotal

            # Convertimos el diccionario a un DataFrame
            if diccionario_ventas:
                df_productos = pd.DataFrame.from_dict(diccionario_ventas, orient='index').reset_index()
                df_productos.rename(columns={'index': 'Producto'}, inplace=True)
                df_productos = df_productos.sort_values(by="Monto Total (S/.)", ascending=False)
            else:
                df_productos = pd.DataFrame(columns=["Producto", "Cantidad", "Monto Total (S/.)", "Categoría"])

            # --- 2. EXPANDER: ANÁLISIS FINANCIERO ---
            with st.expander("💰 Panel de Análisis Financiero", expanded=True):
                st.metric("Total Ingresos Reales (Rango Seleccionado)", f"S/. {total_ingresos:.2f}")
                st.markdown("---")
                st.markdown("#### 📊 Desglose por Forma de Pago")
                
                desglose_pagos = {}
                for p in ingresos_validos:
                    metodo_raw = str(p.get('metodo_pago', 'No especificado')).strip()
                    metodo = metodo_raw.title() if metodo_raw else "No especificado"
                    monto = float(p.get('monto_total', 0))
                    desglose_pagos[metodo] = desglose_pagos.get(metodo, 0.0) + monto
                
                if desglose_pagos:
                    cols_pagos = st.columns(len(desglose_pagos))
                    for i, (metodo, monto) in enumerate(desglose_pagos.items()):
                        with cols_pagos[i]:
                            icono = "💳"
                            if "Efectivo" in metodo: icono = "💵"
                            elif "Yape" in metodo or "Plin" in metodo: icono = "📱"
                            st.metric(f"{icono} {metodo}", f"S/. {monto:.2f}")
                
                st.divider()
                st.markdown(f"**Total de pedidos en el rango:** `{len(pedidos_rango)}` (Cortesías: `{len(pedidos_rango) - len(ingresos_validos)}`)")

            # --- 3. EXPANDER: MATRIZ DE VENTAS POR PRODUCTO ---
            with st.expander("🍔 Matriz de Ventas por Producto", expanded=False):
                if not df_productos.empty:
                    df_mostrar = df_productos.drop(columns=["Categoría"]).copy()
                    df_mostrar["Monto Total (S/.)"] = df_mostrar["Monto Total (S/.)"].map(lambda x: f"S/. {x:,.2f}")
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay productos vendidos en este rango de fechas.")

            # --- 4. EXPANDER: GRÁFICOS VISUALES (DIVIDIDOS POR PESTAÑAS) ---
            with st.expander("📈 Gráficos de Distribución", expanded=False):
                import plotly.express as px
                fig_pie_prin = None
                fig_pie_beb = None
                
                if not df_productos.empty:
                    df_prin = df_productos[df_productos["Categoría"] == "Principales"]
                    df_beb = df_productos[df_productos["Categoría"] == "Bebidas"]
                    
                    tab_prin, tab_beb = st.tabs(["🍔 Productos Principales", "🥤 Bebidas"])
                    
                    # Pestaña de Productos Principales
                    with tab_prin:
                        if not df_prin.empty:
                            cg1, cg2 = st.columns(2)
                            with cg1:
                                st.markdown("**Distribución de Ingresos (%)**")
                                fig_pie_prin = px.pie(df_prin, values='Monto Total (S/.)', names='Producto', hole=0.4)
                                fig_pie_prin.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                                st.plotly_chart(fig_pie_prin, use_container_width=True)
                            with cg2:
                                st.markdown("**Cantidades Vendidas**")
                                df_bar_prin = df_prin.set_index('Producto')
                                st.bar_chart(df_bar_prin['Cantidad'], color="#ff4b4b") # Color Rojo
                        else:
                            st.info("No hay registros de ventas para productos principales.")
                            
                    # Pestaña de Bebidas
                    with tab_beb:
                        if not df_beb.empty:
                            cg3, cg4 = st.columns(2)
                            with cg3:
                                st.markdown("**Distribución de Ingresos (%)**")
                                fig_pie_beb = px.pie(df_beb, values='Monto Total (S/.)', names='Producto', hole=0.4)
                                fig_pie_beb.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                                st.plotly_chart(fig_pie_beb, use_container_width=True)
                            with cg4:
                                st.markdown("**Cantidades Vendidas**")
                                df_bar_beb = df_beb.set_index('Producto')
                                st.bar_chart(df_bar_beb['Cantidad'], color="#00a2ed") # Color Azul
                        else:
                            st.info("No hay registros de ventas para bebidas.")
                else:
                    st.info("No hay datos suficientes para generar gráficos.")

            # --- 5. EXPANDER: CENTRO DE EXPORTACIÓN ---
            with st.expander("📥 Centro de Exportación de Reportes", expanded=False):
                st.markdown("Seleccione el formato y tipo de información que desea exportar:")
                ce1, ce2, ce3 = st.columns(3)
                
                # Reporte 1: Excel de Ventas Generales
                with ce1:
                    datos_exportacion = []
                    for p in pedidos_rango:
                        datos_exportacion.append({
                            "Código": p.get('codigo_exacta', ''),
                            "Fecha / Hora": p.get('created_at', ''),
                            "Cliente": p.get('cliente', ''),
                            "Destino / Mesa": p.get('destino_entrega', ''),
                            "Método de Pago": p.get('metodo_pago', ''),
                            "Monto Total (S/.)": float(p.get('monto_total', 0)),
                            "Cortesía": p.get('cortesia', 'No'),
                        })
                    df_reporte = pd.DataFrame(datos_exportacion)
                    out_excel_1 = io.BytesIO()
                    with pd.ExcelWriter(out_excel_1, engine='openpyxl') as writer:
                        df_reporte.to_excel(writer, index=False, sheet_name='Ventas')
                    
                    st.download_button(
                        label="📄 Exportar Lista de Ventas (.xlsx)",
                        data=out_excel_1.getvalue(),
                        file_name=f"Ventas_{fecha_inicio.strftime('%d%m%Y')}_al_{fecha_fin.strftime('%d%m%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                # Reporte 2: Excel de Productos Vendidos
                with ce2:
                    out_excel_2 = io.BytesIO()
                    with pd.ExcelWriter(out_excel_2, engine='openpyxl') as writer:
                        df_productos.drop(columns=["Categoría"], errors="ignore").to_excel(writer, index=False, sheet_name='Productos')
                    
                    st.download_button(
                        label="🍔 Exportar Productos Vendidos (.xlsx)",
                        data=out_excel_2.getvalue(),
                        file_name=f"Productos_Vendidos_{fecha_inicio.strftime('%d%m%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                # Reporte 3: Gráficos en HTML (Imprimible a PDF)
                with ce3:
                    html_graficos = ""
                    if fig_pie_prin is not None:
                        html_graficos += f"<h3>Distribución: Productos Principales</h3>{fig_pie_prin.to_html(full_html=False, include_plotlyjs='cdn')}"
                    if fig_pie_beb is not None:
                        html_graficos += f"<h3>Distribución: Bebidas</h3>{fig_pie_beb.to_html(full_html=False, include_plotlyjs='cdn')}"
                        
                    if html_graficos != "":
                        html_content = f"""
                        <html>
                        <head>
                            <title>Reporte de Ventas La Exacta</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                                th {{ background-color: #f2f2f2; }}
                            </style>
                        </head>
                        <body>
                            <h2>Reporte Comercial: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}</h2>
                            <h3>1. Matriz de Productos Vendidos</h3>
                            {df_productos.drop(columns=["Categoría"], errors="ignore").to_html(index=False)}
                            <h2>2. Gráficos de Ingresos</h2>
                            {html_graficos}
                            <p style="text-align: center; color: #888;"><i>Para guardar como PDF, presione Ctrl + P y seleccione 'Guardar como PDF'</i></p>
                        </body>
                        </html>
                        """
                        st.download_button(
                            label="📈 Exportar Reporte + Gráficos (HTML/PDF)",
                            data=html_content,
                            file_name=f"Dashboard_Graficos_{fecha_inicio.strftime('%d%m%Y')}.html",
                            mime="text/html",
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.button("📈 Exportar Reporte + Gráficos (HTML/PDF)", disabled=True, use_container_width=True)

        else:
            st.info("No se encontraron registros de ventas en las fechas seleccionadas.")
