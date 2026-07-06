import streamlit as st
import pandas as pd
from database import conectar, obtener_productos

def mostrar_modulo_pedidos():
    # Inicializar las variables de estado en memoria de forma segura
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    if 'paso_pedido' not in st.session_state:
        st.session_state.paso_pedido = 1  # 1: Selección, 2: Pasarela de Pago

    st.header("🛒 Terminal de Pedidos La Exacta")
    
    # --- CONTROL DE IDENTIFICACIÓN (Estilo KFC / Bembos / Counter) ---
    nombre_cliente = st.text_input(
        "👤 Nombre del Cliente / N° Mesa:", 
        value=st.session_state.get('cliente_actual', ''),
        placeholder="Ej: Juan Perez / Mesa 4 - Llevar"
    )
    st.session_state['cliente_actual'] = nombre_cliente

    # --- PASO 1: VISTA DE CARTA DIGITAL CON ADICIONALES ---
    if st.session_state.paso_pedido == 1:
        res = obtener_productos()
        
        if res.data:
            # Segmentamos los productos normales/combos de los complementos/adicionales
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
                        
                        # --- VENTANA EMERGENTE DE COMPLEMENTOS (POPOVER OPTIMIZADO) ---
                        adicionales_seleccionados = []
                        with st.popover("➕ Agregar Complementos / Salsas", use_container_width=True):
                            st.caption("Selecciona los adicionales para este producto:")
                            for comp in complementos:
                                precio_comp = f"(+ S/. {comp['precio_venta']:.2f})" if comp['precio_venta'] > 0 else "(Gratis)"
                                # CORREGIDO: Sintaxis limpia y segura del key único
                                if st.checkbox(f"{comp['nombre']} {precio_comp}", key=f"comp_{p['id']}_{comp['id']}"):
                                    adicionales_seleccionados.append({
                                        "nombre": comp['nombre'],
                                        "precio": float(comp['precio_venta'])
                                    })
                    
                    with c3:
                        cant = st.number_input("Cant", min_value=1, max_value=10, key=f"cant_{p['id']}")
                        if st.button("🛒 Agregar", key=f"btn_{p['id']}", use_container_width=True, type="primary"):
                            # Validación obligatoria del nombre del cliente
                            if not st.session_state['cliente_actual'].strip():
                                st.error("⚠️ Ingrese el nombre del cliente en la parte superior antes de agregar.")
                            else:
                                # Inyección estructurada al carrito
                                st.session_state.carrito.append({
                                    "id_producto": p['id'],
                                    "nombre": p['nombre'],
                                    "precio_base": float(p['precio_venta']),
                                    "cantidad": cant,
                                    "adicionales": adicionales_seleccionados
                                })
                                st.success(f"✅ {p['nombre']} agregado")
                                st.rerun()

            # --- DESPLIEGUE LATERAL O COMPACTO DEL CARRITO DE COMPRAS ---
            if st.session_state.carrito:
                st.divider()
                st.subheader(f"🛍️ Carrito de: {st.session_state['cliente_actual']}")
                total = 0.0
                
                for i, item in enumerate(st.session_state.carrito):
                    # Sumatoria matemática: Precio base + suma de sus adicionales individuales
                    precio_adicionales = sum(a['price'] for a in item['adicionales']) if 'price' in item['adicionales'] else sum(a['precio'] for a in item['adicionales'])
                    costo_unitario_total = item['precio_base'] + precio_adicionales
                    subtotal = costo_unitario_total * item['cantidad']
                    total += subtotal
                    
                    # Detalle visual en pantalla
                    texto_item = f"**{item['cantidad']}x {item['nombre']}** - S/. {subtotal:.2f}"
                    st.write(texto_item)
                    if item['adicionales']:
                        nombres_ad = ", ".join([a['nombre'] for a in item['adicionales']])
                        st.caption(f"➕ Adicionales: {nombres_ad}")
                        
                    if st.button("🗑️ Quitar", key=f"del_car_{i}"):
                        st.session_state.carrito.pop(i)
                        st.rerun()
                
                st.divider()
                st.metric("Total a Pagar", f"S/. {total:.2f}")
                if st.button("✅ Procesar Pago e Imprimir", use_container_width=True, type="primary"):
                    st.session_state.paso_pedido = 2
                    st.rerun()
        else:
            st.info("No hay productos vigentes en la carta.")

    # --- PASO 2: PASARELA DE PAGO / CIERRE DE CAJA ---
    elif st.session_state.paso_pedido == 2:
        st.header("💳 Finalizar Pedido")
        if st.button("⬅️ Volver a la Carta"):
            st.session_state.paso_pedido = 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Datos de Despacho")
            st.write(f"Cliente: **{st.session_state['cliente_actual']}**")
            pago = st.radio("Método de Pago:", ["Yape / Plin", "Tarjeta (Tukuy)", "Efectivo"])
            whatsapp = st.text_input("WhatsApp de contacto", placeholder="999888777")
        
        with col2:
            # Re-cálculo exacto del monto acumulado para el cobro
            total_final = 0.0
            for item in st.session_state.carrito:
                p_ad = sum(a['precio'] for a in item['adicionales'])
                total_final += (item['precio_base'] + p_ad) * item['cantidad']
                
            st.metric("Monto Total a Cobrar", f"S/. {total_final:.2f}")
            
            if st.button("🔥 Confirmar Transmisión de Pedido", use_container_width=True, type="primary"):
                # Aquí se conectará con el backend de Supabase y el disparador de la ticketera ADV-8011N
                st.success(f"🎉 ¡Pedido de {st.session_state['cliente_actual']} registrado correctamente!")
                st.session_state.carrito = []
                st.session_state.paso_pedido = 1
                st.rerun()
