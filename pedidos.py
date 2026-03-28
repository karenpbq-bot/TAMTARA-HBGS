import streamlit as st
import pandas as pd
from database import conectar, obtener_productos

def mostrar_modulo_pedidos():
    # Inicializar el carrito en la sesión si no existe
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    if 'paso_pedido' not in st.session_state:
        st.session_state.paso_pedido = 1 # 1: Selección, 2: Pago

    # --- PASO 1: SELECCIÓN DE PRODUCTOS Y COMBOS ---
    if st.session_state.paso_pedido == 1:
        st.header("🛒 Arma tu Pedido")
        res = obtener_productos()
        
        if res.data:
            # Filtrar solo productos vigentes
            productos = [p for p in res.data if p.get('vigente', True)]
            
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
                    with c3:
                        cant = st.number_input("Cantidad", min_value=0, max_value=10, key=f"cant_{p['id']}")
                        if st.button("Añadir ➕", key=f"add_{p['id']}"):
                            if cant > 0:
                                st.session_state.carrito.append({
                                    "id": p['id'], "nombre": p['nombre'], 
                                    "precio": p['precio_venta'], "cantidad": cant
                                })
                                st.toast(f"Añadido: {p['nombre']}")

        # Barra lateral del Carrito
        with st.sidebar:
            st.header("📋 Resumen")
            total = 0
            for i, item in enumerate(st.session_state.carrito):
                subtotal = item['precio'] * item['cantidad']
                total += subtotal
                st.write(f"{item['cantidad']}x {item['nombre']} - S/. {subtotal:.2f}")
                if st.button("❌", key=f"del_car_{i}"):
                    st.session_state.carrito.pop(i)
                    st.rerun()
            
            st.divider()
            st.subheader(f"Total: S/. {total:.2f}")
            if total > 0:
                if st.button("✅ Ir a Pagar", use_container_width=True):
                    st.session_state.paso_pedido = 2
                    st.rerun()

    # --- PASO 2: PASARELA DE PAGO ---
    elif st.session_state.paso_pedido == 2:
        st.header("💳 Finalizar Pedido")
        if st.button("⬅️ Volver a la Carta"):
            st.session_state.paso_pedido = 1
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Método de Pago")
            pago = st.radio("Seleccione:", ["Yape / Plin", "Tarjeta (Tukuy)", "Efectivo"])
            st.text_input("Nombre de quien recoge")
            st.text_input("WhatsApp de contacto")
        
        with col2:
            total_final = sum(item['precio'] * item['cantidad'] for item in st.session_state.carrito)
            st.metric("Monto Total", f"S/. {total_final:.2f}")
            if st.button("🚀 Confirmar Pedido", type="primary", use_container_width=True):
                st.balloons()
                st.success("¡Pedido enviado a cocina!")
                st.session_state.carrito = []
                st.session_state.paso_pedido = 1
