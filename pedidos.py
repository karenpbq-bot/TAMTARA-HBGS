import streamlit as st
import pandas as pd
from database import conectar, obtener_productos

def mostrar_modulo_pedidos():
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    if 'paso_pedido' not in st.session_state:
        st.session_state.paso_pedido = 1 

    # --- CONTROL DE IDENTIFICACIÓN (Estilo KFC / Bembos) ---
    st.header("🛒 Terminal de Pedidos HBGS")
    
    # El nombre se registra desde el inicio para que el counter o el cliente queden indexados
    nombre_cliente = st.text_input("👤 Nombre del Cliente / N° Mesa:", 
                                   value=st.session_state.get('cliente_actual', ''),
                                   placeholder="Ej: Juan Perez / Mesa 4")
    st.session_state['cliente_actual'] = nombre_cliente

    if st.session_state.paso_pedido == 1:
        res = obtener_productos()
        
        if res.data:
            # Separamos platos principales de los adicionales/complementos
            productos = [p for p in res.data if p.get('vigente', True) and p.get('categoria') != 'Complementos']
            complementos = [c for c in res.data if c.get('vigente', True) and c.get('categoria') == 'Complementos']
            
            for p in productos:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        img = p['imagen_url'] if p['imagen_url'] else "https://via.placeholder.com/150"
                        st.image(img, use_container_width=True)
                    with c2:
                        etiqueta_combo = " 🍟 [COMBO]" if p.get('es_combo') else \"\"
                        st.subheader(f"{p['nombre']}{etiqueta_combo}")
                        st.write(p['descripcion'])
                        st.write(f"**S/. {p['precio_venta']:.2f}**")
                        
                        # --- VENTANA EMERGENTE PARA ADICIONALES (POPOVER) ---
                        adicionales_seleccionados = []
                        with st.popover("➕ Agregar Complementos / Salsas", use_container_width=True):
                            st.caption("Selecciona los adicionales para este producto:")
                            for comp in complementos:
                                precio_comp = f"(+ S/. {comp['precio_venta']:.2f})" if comp['precio_venta'] > 0 else "(Gratis)"
                                if st.checkbox(f"{comp['nombre']} {precio_comp}", key=f"comp_{p['id']}_{comp['id'] concrete}"):
                                    adicionales_seleccionados.append({
                                        "nombre": comp['nombre'],
                                        "precio": float(comp['precio_venta'])
                                    })
                    
                    with c3:
                        cant = st.number_input("Cant", min_value=1, max_value=10, key=f"cant_{p['id']}")
                        if st.button("🛒 Agregar", key=f"btn_{p['id']}", use_container_width=True, type="primary"):
                            if not st.session_state['cliente_actual'].strip():
                                st.error("⚠️ Por favor, ingrese el nombre del cliente antes de agregar productos.");
                            else:
                                # Inyección estructurada al carrito de la sesión
                                st.session_state.carrito.append({
                                    "id_producto": p['id'],
                                    "nombre": p['nombre'],
                                    "precio_base": float(p['precio_venta']),
                                    "cantidad": cant,
                                    "adicionales": adicionales_seleccionados
                                })
                                st.success(f"✅ {p['nombre']} agregado")
                                st.rerun()
