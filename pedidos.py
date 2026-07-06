import streamlit as st
import pandas as pd
from database import conectar, obtener_productos

def mostrar_modulo_pedidos():
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    if 'paso_pedido' not in st.session_state:
        st.session_state.paso_pedido = 1 

    st.header("🛒 Terminal de Pedidos La Exacta")
    db = conectar()
    
    # --- FLUJO COUNTER / FAST FOOD: IDENTIFICACIÓN INICIAL EN FILA ---
    nombre_cliente = st.text_input(
        "👤 Nombre del Cliente:", 
        value=st.session_state.get('cliente_actual', ''),
        placeholder="Ej: Juan Perez"
    )
    st.session_state['cliente_actual'] = nombre_cliente

    # Selección de Tipo de Entrega
    tipo_ent = st.radio("Tipo de Entrega:", ["Mesa / Salón", "Delivery / Llevar"], horizontal=True)
    
    if tipo_ent == "Mesa / Salón":
        destino = st.text_input("N° Mesa:", placeholder="Ej: Mesa 4")
        telefono = ""
    else:
        destino = st.text_input("Dirección de Despacho (Si es delivery):", placeholder="Ej: Av. Principal 123 o 'Llevar'")
        telefono = st.text_input("Teléfono de Contacto:", placeholder="Ej: 999888777")

    # --- PASO 1: SELECCIÓN DE PRODUCTOS Y ADICIONALES ---
    if st.session_state.paso_pedido == 1:
        res = obtener_productos()
        
        if res.data:
            productos = [p for p in res.data if p.get('vigente', True) and p.get('categoria') != 'Complementos']
            complementos = [c for c in res.data if c.get('vigente', True) and c.get('categoria') == 'Complementos']
            
            for p in productos:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        img = p['imagen_url'] if p['imagen_url'] else "https://via.placeholder.com/150"
                        st.image(img, use_container_width=True)
                    with c2:
                        etiqueta_combo = " 🍟 [COMBO]" if p.get('es_combo') else ""
                        st.subheader(f"{p['nombre']}{etiqueta_combo}")
                        st.write(p['descripcion'])
                        st.write(f"**S/. {p['precio_venta']:.2f}**")
                        
                        # Popover de adicionales modulado
                        adicionales_seleccionados = []
                        with st.popover("➕ Adicionales / Salsas", use_container_width=True):
                            for comp in complementos:
                                precio_comp = f"(+ S/. {comp['precio_venta']:.2f})" if comp['precio_venta'] > 0 else "(Gratis)"
                                if st.checkbox(f"{comp['nombre']} {precio_comp}", key=f"comp_{p['id']}_{comp['id']}"):
                                    adicionales_seleccionados.append({
                                        "nombre": comp['nombre'],
                                        "precio": float(comp['precio_venta'])
                                    })
                    
                    with c3:
                        cant = st.number_input("Cant", min_value=1, max_value=10, key=f"cant_{p['id']}")
                        if st.button("🛒 Agregar", key=f"btn_{p['id']}", use_container_width=True, type="primary"):
                            if not st.session_state['cliente_actual'].strip():
                                st.error("⚠️ Ingrese el nombre del cliente arriba antes de agregar.")
                            else:
                                st.session_state.carrito.append({
                                    "id_producto": p['id'],
                                    "nombre": p['nombre'],
                                    "precio_base": float(p['precio_venta']),
                                    "cantidad": cant,
                                    "adicionales": adicionales_seleccionados
                                })
                                st.success(f"✅ {p['nombre']} agregado")
                                st.rerun()

            # Vista interna del Carrito en Caja
            if st.session_state.carrito:
                st.divider()
                st.subheader("🛍️ Lista de Compra Actual")
                total = 0.0
                for i, item in enumerate(st.session_state.carrito):
                    p_ad = sum(a['precio'] for a in item['adicionales'])
                    subtotal = (item['precio_base'] + p_ad) * item['cantidad']
                    total += subtotal
                    st.write(f"**{item['cantidad']}x {item['nombre']}** - S/. {subtotal:.2f}")
                    if item['adicionales']:
                        st.caption(f"  └ Adicionales: {', '.join([a['nombre'] for a in item['adicionales']])}")
                    if st.button("Quitar 🗑️", key=f"del_{i}"):
                        st.session_state.carrito.pop(i)
                        st.rerun()
                
                st.divider()
                st.metric("Total Acumulado", f"S/. {total:.2f}")
                if st.button("💳 Ir al Cierre de Caja", use_container_width=True, type="primary"):
                    st.session_state.paso_pedido = 2
                    st.rerun()

    # --- PASO 2: CONTROL DE COBRO Y EMISIÓN DE TICKETS ESC/POS ---
    elif st.session_state.paso_pedido == 2:
        st.subheader("💳 Cierre y Validación del Pago")
        if st.button("⬅️ Volver a la Carta"):
            st.session_state.paso_pedido = 1
            st.rerun()

        total_final = 0.0
        for item in st.session_state.carrito:
            p_ad = sum(a['precio'] for a in item['adicionales'])
            total_final += (item['precio_base'] + p_ad) * item['cantidad']

        c_pago1, c_pago2 = st.columns(2)
        
        with c_pago1:
            st.metric("Monto Total a Cobrar", f"S/. {total_final:.2f}")
            metodo = st.radio("Forma de Pago Registrada:", ["Efectivo", "Yape / Plin", "Tarjeta"])
            
            num_op = None
            monto_rec = None
            vuelto = 0.0
            
            if metodo in ["Yape / Plin", "Tarjeta"]:
                num_op = st.text_input("N° de Operación (Obligatorio):", placeholder="Ej: 198273 o Ref. Banco")
            else:
                monto_rec = st.number_input("Monto en efectivo recibido:", min_value=float(total_final), step=1.0)
                vuelto = monto_rec - total_final
                st.subheader(f"💵 Vuelto Exacto: S/. {vuelto:.2f}")

        with c_pago2:
            st.write("### Datos de Auditoría")
            st.info(f"**Cliente:** {st.session_state['cliente_actual']}\n\n**Despacho:** {destino if destino else 'No indicado'}")
            
            # Botón maestro de transmisión
            if st.button("🔥 CONFIRMAR COBRO Y EMITIR COMANDAS", use_container_width=True, type="primary"):
                if metodo in ["Yape / Plin", "Tarjeta"] and not num_op:
                    st.error("⚠️ Para pagos electrónicos debe registrar el número de operación bancaria.")
                else:
                    # 1. Inserción en Supabase
                    pedido_payload = {
                        "cliente": st.session_state['cliente_actual'],
                        "tipo_entrega": "Mesa" if tipo_ent == "Mesa / Salón" else "Delivery",
                        "destino_entrega": destino,
                        "telefono_contacto": telefono,
                        "items": st.session_state.carrito,
                        "metodo_pago": metodo,
                        "monto_total": total_final,
                        "num_operacion": num_op,
                        "monto_recibido": monto_rec,
                        "vuelto": vuelto,
                        "estado": "En cocina"
                    }
                    
                    res_db = db.table("pedidos").insert(pedido_payload).execute()
                    id_pedido = res_db.data[0]['id'] if res_db.data else 999
                    
                    # 2. DETONADOR DE IMPRESIÓN ADANCE ADV-8011N (ESC/POS 300mm/s)
                    # Aquí generamos el log de transmisión en crudo separado por comandos de corte automático \x1b\x69
                    st.success(f"🎉 Pedido N° {id_pedido} guardado en la base de datos.")
                    
                    with st.spinner("Transmitiendo buffers a la ticketera Advance..."):
                        st.code(f"""
                        === ENVIANDO AL BUFFER DE LA IMPRESORA ADVANCE ADV-8011N ===
                        
                        [TICKET 1: COMPROBANTE DE PEDIDO]
                        LA EXACTA HAMBURGUESERÍA
                        Pedido N°: {id_pedido}
                        Cliente: {st.session_state['cliente_actual']}
                        -----------------------------------------
                        {chr(10).join([f"{i['cantidad']}x {i['nombre']} - S/. {i['precio_base']:.2f}" for i in st.session_state.carrito])}
                        -----------------------------------------
                        TOTAL PAGADO: S/. {total_final:.2f}
                        Método: {metodo} {f'(Op: {num_op})' if num_op else ''}
                        \x1b\x69 <-- COMANDO DE CORTE DE PAPEL TICKET 1
                        
                        [TICKET 2: DESPACHO / MESA / DELIVERY]
                        LA EXACTA - LOGÍSTICA
                        Pedido N°: {id_pedido}
                        Cliente: {st.session_state['cliente_actual']}
                        Entrega: {tipo_ent}
                        Destino: {destino}
                        Contacto: {telefono if telefono else 'N/A'}
                        \x1b\x69 <-- COMANDO DE CORTE DE PAPEL TICKET 2
                        
                        [TICKET 3: COMANDA DE COCINA]
                        🔥 ¡NUEVA ORDEN DE COCINA! 🔥
                        Pedido N°: {id_pedido}
                        -----------------------------------------
                        {chr(10).join([f"[{i['cantidad']}] X  {i['nombre']} {chr(10)+'   └ Adicionales: '+', '.join([a['nombre'] for a in i['adicionales']]) if i['adicionales'] else ''}" for i in st.session_state.carrito])}
                        -----------------------------------------
                        \x1b\x69 <-- COMANDO DE CORTE DE PAPEL TICKET 3
                        """)
                    
                    st.balloons()
                    st.session_state.carrito = []
                    st.session_state.paso_pedido = 1
                    st.rerun()
