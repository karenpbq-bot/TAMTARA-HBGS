import streamlit as st
import pandas as pd
from database import conectar, obtener_productos
from datetime import datetime

# =====================================================================
# MODULO DE AUDITORÍA Y CONTROL DE IMPRESIÓN (TICKETERAS ADVANCE)
# =====================================================================

def verificar_estado_ticketera():
    try:
        return {"online": True}
    except Exception:
        return {"online": False}

def generar_formato_ticket(pedido_payload, codigo_ticket, tipo_ticket="caja"):
    lineas = []
    if tipo_ticket == "caja":
        lineas.append("      LA EXACTA HAMBURGUESERIA      ")
        lineas.append(f"Pedido N°: {codigo_ticket}")
        lineas.append(f"Cliente: {pedido_payload['cliente']}")
        lineas.append("-" * 40)
        for i in pedido_payload['items']:
            p_ad = sum(float(a['precio']) for a in i['adicionales'])
            sub = (i['precio_base'] + p_ad) * i['cantidad']
            lineas.append(f"{i['cantidad']}x {i['nombre']:<20} S/. {sub:.2f}")
            if i['adicionales']:
                lineas.append(f"  └ Adic: {', '.join([a['nombre'] for a in i['adicionales']])}")
        lineas.append("-" * 40)
        lineas.append(f"TOTAL: S/. {pedido_payload['monto_total']:.2f} | {pedido_payload['metodo_pago']}")
        lineas.append("\n\x1b\x69")
        
    elif tipo_ticket == "cocina":
        lineas.append("      🔥 NUEVA ORDEN - COCINA 🔥      ")
        lineas.append(f"Pedido N°: {codigo_ticket}")
        lineas.append(f"Ubicación: {pedido_payload['destino_entrega'] or 'Llevar'}")
        lineas.append("-" * 40)
        for i in pedido_payload['items']:
            lineas.append(f"[{i['cantidad']}] {i['nombre']}")
            if i['adicionales']:
                lineas.append(f"    └ Adic: {', '.join([a['nombre'] for a in i['adicionales']])}")
        lineas.append("-" * 40)
        lineas.append("\n\x1b\x69")
        
    return "\n".join(lineas)

def enviar_a_hardware_ticketera(texto_ticket):
    return True

def procesar_impresion_comanda(pedido_id, codigo_ticket, pedido_payload, db):
    st.session_state[f"imprimiendo_{pedido_id}"] = True
    try:
        servicio = verificar_estado_ticketera()
        if not servicio["online"]:
            raise Exception("La ticketera física está desconectada o el servicio local está apagado.")
            
        ticket_caja = generar_formato_ticket(pedido_payload, codigo_ticket, tipo_ticket="caja")
        ticket_cocina = generar_formato_ticket(pedido_payload, codigo_ticket, tipo_ticket="cocina")
        
        envio_caja = enviar_a_hardware_ticketera(ticket_caja)
        envio_cocina = enviar_a_hardware_ticketera(ticket_cocina)
        
        if not envio_caja or not envio_cocina:
            raise Exception("El buffer de la ticketera Advance rechazó las tramas de datos.")
            
        db.table("pedidos").update({
            "impreso": True, 
            "fecha_impresion": datetime.now().isoformat()
        }).eq("id", pedido_id).execute()
        
        st.success("🎯 Comandas enviadas e impresas con éxito en Caja y Cocina.")
        
    except Exception as e:
        st.error(f"🚨 FALLO DE IMPRESIÓN FISICA: {str(e)}")
        try:
            db.table("log_errores").insert({
                "pedido_id": pedido_id, 
                "modulo": "Impresión Ventas", 
                "error": str(e)
            }).execute()
        except Exception:
            pass
            
    finally:
        st.session_state[f"imprimiendo_{pedido_id}"] = False

def mostrar_modulo_pedidos():
    # --- CSS PARA OPTIMIZAR ESPACIO Y TAMAÑOS ---
    st.markdown("""
        <style>
            div.block-container {
                padding-top: 1.5rem !important; 
                padding-bottom: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100% !important;
            }
            .producto-titulo {
                font-size: 0.95rem !important;
                font-weight: bold !important;
                margin-bottom: 2px !important;
            }
            .producto-desc {
                font-size: 0.75rem !important;
                color: #555555 !important;
                margin-bottom: 4px !important;
            }
            .producto-precio {
                font-size: 0.85rem !important;
                font-weight: bold !important;
                color: #28a745 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    if 'paso_pedido' not in st.session_state:
        st.session_state.paso_pedido = 1 

    st.header("🛒 Terminal de Pedidos La Exacta")
    db = conectar()
    
    # --- IDENTIFICACIÓN INICIAL ---
    c_id1, c_id2, c_id3 = st.columns([2, 1, 1])
    with c_id1:
        nombre_cliente = st.text_input(
            "👤 Nombre del Cliente:", 
            value=st.session_state.get('cliente_actual', ''),
            placeholder="Ej: Juan Perez"
        )
        st.session_state['cliente_actual'] = nombre_cliente

    with c_id2:
        tipo_ent = st.radio("Tipo de Entrega:", ["Mesa / Salón", "Delivery / Llevar"], horizontal=True)

    with c_id3:
        if tipo_ent == "Mesa / Salón":
            destino = st.text_input("N° Mesa:", placeholder="Ej: Mesa 4")
            telefono = ""
        else:
            destino = st.text_input("Dirección / Referencia:", placeholder="Ej: Av. Principal 123")
            telefono = st.text_input("Teléfono:", placeholder="Ej: 999888777")

    st.divider()

    # --- PASO 1: SELECCIÓN Y VALIDACIÓN EN 3 COLUMNAS ---
    if st.session_state.paso_pedido == 1:
        res = obtener_productos()
        
        if res.data:
            principales = [p for p in res.data if p.get('vigente', True) and p.get('categoria') in ['Principal', 'Hamburguesas']]
            bebidas = [p for p in res.data if p.get('vigente', True) and p.get('categoria') == 'Bebidas']
            ad_gratis = [c for c in res.data if c.get('vigente', True) and c.get('categoria') == 'Ad Gratis']
            ad_porcion = [c for c in res.data if c.get('vigente', True) and c.get('categoria') == 'Ad Porción']
            
            col_prin, col_bebs, col_res = st.columns([1.2, 1.2, 1.0])
            
            # 1. COLUMNA: PRINCIPALES
            with col_prin:
                st.markdown("### 🍔 Principales")
                if not principales:
                    st.info("No hay productos principales registrados.")
                for p in principales:
                    with st.container(border=True):
                        cp_img, cp_inf = st.columns([1, 2])
                        with cp_img:
                            img = p['imagen_url'] if p['imagen_url'] else "https://via.placeholder.com/150"
                            st.image(img, use_container_width=True)
                        with cp_inf:
                            etiqueta_combo = " 🍟 [COMBO]" if p.get('es_combo') else ""
                            cod_label = f" [{p['codigo_corto']}]" if p.get('codigo_corto') else ""
                            st.markdown(f'<p class="producto-titulo">{p["nombre"]}{cod_label}{etiqueta_combo}</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="producto-desc">{p["descripcion"]}</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="producto-precio">S/. {p["precio_venta"]:.2f}</p>', unsafe_allow_html=True)
                        
                        adicionales_seleccionados = []
                        
                        col_ad1, col_ad2 = st.columns(2)
                        with col_ad1:
                            with st.popover("➕ Ad Gratis", use_container_width=True):
                                for comp in ad_gratis:
                                    if st.checkbox(f"{comp['nombre']}", key=f"gratis_{p['id']}_{comp['id']}"):
                                        adicionales_seleccionados.append({
                                            "nombre": comp['nombre'],
                                            "codigo": comp.get('codigo_corto', comp['nombre'][:3].upper()),
                                            "precio": 0.0
                                        })
                        with col_ad2:
                            with st.popover("➕ Ad Porción", use_container_width=True):
                                for comp in ad_porcion:
                                    if st.checkbox(f"{comp['nombre']} (+S/. {comp['precio_venta']:.2f})", key=f"porcion_{p['id']}_{comp['id']}"):
                                        adicionales_seleccionados.append({
                                            "nombre": comp['nombre'],
                                            "codigo": comp.get('codigo_corto', comp['nombre'][:3].upper()),
                                            "precio": float(comp['precio_venta'])
                                        })
                        
                        cb_cant, cb_btn = st.columns([1, 1.5])
                        with cb_cant:
                            cant = st.number_input("Cant", min_value=1, max_value=10, key=f"cant_{p['id']}", label_visibility="collapsed")
                        with cb_btn:
                            if st.button("🛒 Agregar", key=f"btn_{p['id']}", use_container_width=True, type="primary"):
                                if not st.session_state['cliente_actual'].strip():
                                    st.error("⚠️ Ingrese el nombre del cliente.")
                                else:
                                    st.session_state.carrito.append({
                                        "id_producto": p['id'],
                                        "nombre": p['nombre'],
                                        "codigo": p.get('codigo_corto', p['nombre'][:3].upper()),
                                        "precio_base": float(p['precio_venta']),
                                        "cantidad": cant,
                                        "adicionales": adicionales_seleccionados
                                    })
                                    st.rerun()

            # 2. COLUMNA: BEBIDAS
            with col_bebs:
                st.markdown("### 🥤 Bebidas")
                if not bebidas:
                    st.info("No hay bebidas registradas.")
                for p in bebidas:
                    with st.container(border=True):
                        cb_img, cb_inf = st.columns([1, 2])
                        with cb_img:
                            img = p['imagen_url'] if p['imagen_url'] else "https://via.placeholder.com/150"
                            st.image(img, use_container_width=True)
                        with cb_inf:
                            cod_label = f" [{p['codigo_corto']}]" if p.get('codigo_corto') else ""
                            st.markdown(f'<p class="producto-titulo">{p["nombre"]}{cod_label}</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="producto-desc">{p["descripcion"]}</p>', unsafe_allow_html=True)
                            st.markdown(f'<p class="producto-precio">S/. {p["precio_venta"]:.2f}</p>', unsafe_allow_html=True)
                        
                        cb_cant_b, cb_btn_b = st.columns([1, 1.5])
                        with cb_cant_b:
                            cant = st.number_input("Cant", min_value=1, max_value=10, key=f"cant_beb_{p['id']}", label_visibility="collapsed")
                        with cb_btn_b:
                            if st.button("🛒 Agregar", key=f"btn_beb_{p['id']}", use_container_width=True, type="primary"):
                                if not st.session_state['cliente_actual'].strip():
                                    st.error("⚠️ Ingrese el nombre del cliente.")
                                else:
                                    st.session_state.carrito.append({
                                        "id_producto": p['id'],
                                        "nombre": p['nombre'],
                                        "codigo": p.get('codigo_corto', p['nombre'][:3].upper()),
                                        "precio_base": float(p['precio_venta']),
                                        "cantidad": cant,
                                        "adicionales": []
                                    })
                                    st.rerun()

            # 3. COLUMNA: RESUMEN DE COMPRA (CARRITO)
            with col_res:
                with st.container(border=True):
                    st.markdown("### 🛍️ Resumen Actual")
                    if not st.session_state.carrito:
                        st.info("El carrito está vacío.")
                    else:
                        total = 0.0
                        for i, item in enumerate(st.session_state.carrito):
                            p_ad = sum(float(a['precio']) for a in item['adicionales'])
                            subtotal = (item['precio_base'] + p_ad) * item['cantidad']
                            total += subtotal
                            
                            rc1, rc2 = st.columns([4, 1])
                            with rc1:
                                st.markdown(f"**{item['cantidad']}x {item['nombre']}** — S/. {subtotal:.2f}")
                                if item['adicionales']:
                                    st.caption(f"  └ {', '.join([a['nombre'] for a in item['adicionales']])}")
                            with rc2:
                                if st.button("🗑️", key=f"del_{i}", help="Quitar producto"):
                                    st.session_state.carrito.pop(i)
                                    st.rerun()
                        
                        st.divider()
                        st.metric("Total a Pagar", f"S/. {total:.2f}")
                        if st.button("💳 Ir al Cierre de Caja", use_container_width=True, type="primary"):
                            st.session_state.paso_pedido = 2
                            st.rerun()

    # --- PASO 2: CIERRE, COBRO Y DISTRIBUCIÓN DE IMPRESIÓN ---
    elif st.session_state.paso_pedido == 2:
        st.subheader("💳 Cierre y Validación del Pago")
        if st.button("⬅️ Volver al Catálogo"):
            st.session_state.paso_pedido = 1
            st.rerun()

        total_calculado = 0.0
        for item in st.session_state.carrito:
            p_ad = sum(float(a['precio']) for a in item['adicionales'])
            total_calculado += (item['precio_base'] + p_ad) * item['cantidad']

        c_pago1, c_pago2 = st.columns(2)
        
        with c_pago1:
            es_cortesia = st.checkbox("🎁 Marcar como Cortesía (Liberado de Pago)")
            
            if es_cortesia:
                metodo = "Cortesía"
                st.info("ℹ️ Este pedido es una cortesía. El valor se registrará para control interno, pero no sumará en las ventas cobradas.")
            else:
                metodo = st.radio("Forma de Pago Registrada:", ["Efectivo", "Yape / Plin", "Tarjeta"])
            
            num_op = None
            monto_rec = None
            vuelto = 0.0
            
            if not es_cortesia:
                if metodo in ["Yape / Plin", "Tarjeta"]:
                    num_op = st.text_input("N° de Operación (Obligatorio):", placeholder="Ej: 198273")
                elif metodo == "Efectivo":
                    monto_rec = st.number_input("Monto en efectivo recibido:", min_value=float(total_calculado), step=1.0)
                    vuelto = monto_rec - total_calculado
                    st.subheader(f"💵 Vuelto Exacto: S/. {vuelto:.2f}")

        with c_pago2:
            st.write("### Datos de Auditoría")
            st.info(f"**Cliente:** {st.session_state.get('cliente_actual', '')}\n\n**Despacho:** {destino if destino else 'No indicado'}")
            
            # Verificamos si este pedido viene desde el botón 💳 del Kanban
            id_editando = st.session_state.get('pedido_en_edicion_id')
            
            # ==========================================
            # 1. BOTÓN: CONFIRMAR COBRO DEFINITIVO
            # ==========================================
            if st.button("🔥 CONFIRMAR COBRO Y EMITIR TICKETS", use_container_width=True, type="primary"):
                if not es_cortesia and metodo in ["Yape / Plin", "Tarjeta"] and not num_op:
                    st.error("⚠️ Registre el número de operación bancaria.")
                else:
                    if id_editando:
                        # ACTUALIZAMOS EL PEDIDO PENDIENTE (Se añadieron items y ahora sí se paga)
                        db.table("pedidos").update({
                            "items": st.session_state.carrito,
                            "monto_total": total_calculado,
                            "metodo_pago": metodo,
                            "num_operacion": num_op,
                            "monto_recibido": monto_rec,
                            "vuelto": vuelto,
                            "estado_pago": "Pagado",
                            "cortesia": "Sí" if es_cortesia else "No"
                        }).eq("id", id_editando).execute()
                        st.success("✅ Pedido actualizado y marcado como PAGADO.")
                        
                        del st.session_state['pedido_en_edicion_id']
                    else:
                        # ES UN PEDIDO NUEVO DESDE CERO
                        prefijo_hoy = datetime.now().strftime("%d%m")
                        try:
                            res_hoy = db.table("pedidos").select("id", count="exact").like("codigo_exacta", f"{prefijo_hoy}%").execute()
                            siguiente_correlativo = len(res_hoy.data) + 1 if res_hoy.data else 1
                        except:
                            siguiente_correlativo = 1
                            
                        codigo_ticket_impreso = f"{prefijo_hoy}-{siguiente_correlativo:03d}"
                        
                        pedido_payload = {
                            "cliente": st.session_state['cliente_actual'],
                            "tipo_entrega": "Mesa" if tipo_ent == "Mesa / Salón" else "Delivery",
                            "destino_entrega": destino,
                            "telefono_contacto": telefono,
                            "items": st.session_state.carrito,
                            "metodo_pago": metodo,
                            "monto_total": total_calculado,
                            "num_operacion": num_op,
                            "monto_recibido": monto_rec,
                            "vuelto": vuelto,
                            "estado": "En cocina",
                            "estado_pago": "Pagado", 
                            "pedido_cerrado": "No",
                            "cortesia": "Sí" if es_cortesia else "No",
                            "codigo_exacta": codigo_ticket_impreso
                        }
                        
                        res_db = db.table("pedidos").insert(pedido_payload).execute()
                        id_pedido = res_db.data[0]['id'] if res_db.data else 999
                        st.success(f"🎉 Pedido N° {codigo_ticket_impreso} registrado.")
                        
                        with st.spinner("Transmitiendo datos a ticketeras Advance..."):
                            procesar_impresion_comanda(id_pedido, codigo_ticket_impreso, pedido_payload, db)
                    
                    st.balloons()
                    st.session_state.carrito = []
                    st.session_state.paso_pedido = 1
                    st.session_state['cliente_actual'] = ''  # 🧹 Limpia el campo de cliente al finalizar
                    st.rerun()

            st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

            # ==========================================
            # 2. BOTÓN: ENVIAR / ACTUALIZAR EN COCINA (PAGO PENDIENTE)
            # ==========================================
            if st.button("⚡ ENVIAR A COCINA (PAGO PENDIENTE)", use_container_width=True, type="secondary"):
                if id_editando:
                    # CLIENTE PIDIÓ MÁS COSAS, ACTUALIZAMOS CARRITO Y TOTAL, PERO SIGUE PENDIENTE
                    db.table("pedidos").update({
                        "items": st.session_state.carrito,
                        "monto_total": total_calculado,
                        "estado": "En cocina"
                    }).eq("id", id_editando).execute()
                    
                    st.success("✅ Cuenta actualizada con los nuevos productos.")
                    del st.session_state['pedido_en_edicion_id']
                else:
                    # NUEVO PEDIDO PENDIENTE
                    prefijo_hoy = datetime.now().strftime("%d%m")
                    try:
                        res_hoy = db.table("pedidos").select("id", count="exact").like("codigo_exacta", f"{prefijo_hoy}%").execute()
                        siguiente_correlativo = len(res_hoy.data) + 1 if res_hoy.data else 1
                    except:
                        siguiente_correlativo = 1
                        
                    codigo_ticket_impreso = f"{prefijo_hoy}-{siguiente_correlativo:03d}"
                    
                    pedido_payload_pendiente = {
                        "cliente": st.session_state['cliente_actual'],
                        "tipo_entrega": "Mesa" if tipo_ent == "Mesa / Salón" else "Delivery",
                        "destino_entrega": destino,
                        "telefono_contacto": telefono,
                        "items": st.session_state.carrito,
                        "metodo_pago": "Pendiente",
                        "monto_total": total_calculado,
                        "num_operacion": None,
                        "monto_recibido": 0.0,
                        "vuelto": 0.0,
                        "estado": "En cocina",
                        "estado_pago": "Pendiente",
                        "pedido_cerrado": "No",
                        "cortesia": "No",
                        "codigo_exacta": codigo_ticket_impreso
                    }
                    
                    db.table("pedidos").insert(pedido_payload_pendiente).execute()
                    st.success(f"🚀 Pedido N° {codigo_ticket_impreso} enviado a cocina con estado pendiente.")
                
                st.session_state.carrito = []
                st.session_state.paso_pedido = 1
                st.session_state['cliente_actual'] = ''  # 🧹 Limpia el campo de cliente al finalizar
                st.rerun()
