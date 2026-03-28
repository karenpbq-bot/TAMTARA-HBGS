import streamlit as st
from database import conectar
from login import login_manager
from pedidos import mostrar_modulo_pedidos
from costos import mostrar_modulo_costos
from recetas import mostrar_modulo_recetas
from carta import mostrar_modulo_carta

# Configuración de la página (debe ser la primera orden de Streamlit)
st.set_page_config(page_title="HBGS", layout="wide", page_icon="🍔")

# 1. Ejecutar Login
autenticado, rol = login_manager()

if autenticado:
    if rol == 'admin':
        # Menú Completo para Karen
        menu = st.sidebar.selectbox("Gestión Administrativa", 
            ["Inicio", "Costos (Insumos)", "Recetas (Proyectos)", "Carta", "Pedidos (Ventas)"])
        
        if menu == "Inicio":
            st.write("Bienvenida Karen. Aquí ves el control total.")
        elif menu == "Costos (Insumos)":
            mostrar_modulo_costos()
        elif menu == "Recetas (Proyectos)":
            mostrar_modulo_recetas()
        elif menu == "Carta":
            mostrar_modulo_carta()
        elif menu == "Pedidos (Ventas)":
            mostrar_modulo_pedidos()
            
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    elif rol == 'cliente':
        # --- VISTA CLIENTE (DELIVERY) ---
        # No usamos st.sidebar.selectbox para que no aparezca el menú
        # Solo dejamos un botón discreto para volver si es necesario
        if st.sidebar.button("⬅️ Volver al Inicio"):
            st.session_state.clear()
            st.rerun()
            
        # Lanzamos el módulo de pedidos a pantalla completa
        mostrar_modulo_pedidos()

st.title("🍔 Sistema de Gestión HBGS")

# Menú lateral modular para navegar entre tus negocios
menu = st.sidebar.selectbox("Seleccione un Módulo", 
    ["Inicio", "Costos (Insumos)", "Recetas (Proyectos)", "Carta", "Pedidos", "Inventario"])

if menu == "Inicio":
            st.header("👑 Panel de Administración")
            st.write(f"Bienvenida, Karen. Usa el menú lateral para gestionar HBGS.")
            # Eliminamos métricas de São Paulo y mensajes técnicos

elif menu == "Recetas (Proyectos)":
    mostrar_modulo_recetas()

elif menu == "Carta":
    mostrar_modulo_carta()
    
