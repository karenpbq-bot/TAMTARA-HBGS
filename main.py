import streamlit as st
import os
from database import conectar
from login import login_manager
from pedidos import mostrar_modulo_pedidos
from costos import mostrar_modulo_costos
from recetas import mostrar_modulo_recetas
from carta import mostrar_modulo_carta
from tracking import mostrar_modulo_tracking

# 1. CONFIGURACIÓN DE PÁGINA NATIVA (CORREGIDO: layout="wide" para activar los estilos del tracking)
st.set_page_config(
    page_title="La Exacta",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon=".streamlit/static/logo.png"
)

# 2. Ejecutar el gestor de acceso
autenticado, rol = login_manager()

# 3. Lógica de visualización post-login
if autenticado:
    if rol == 'admin':
        # --- VISTA KAREN (ADMIN) ---
        ruta_logo = os.path.join(os.path.dirname(__file__), ".streamlit", "static", "logo.png")
        if os.path.exists(ruta_logo):
            st.sidebar.image(ruta_logo, use_container_width=True)
            
        st.sidebar.title("🎛️ Panel Admin")
        menu = st.sidebar.selectbox("Seleccione un Módulo", 
            ["Inicio", "Costos (Insumos)", "Recetas (Proyectos)", "Carta", "Pedidos (Ventas)", "Tracking de Pedidos"])
        
        if menu == "Inicio":
            st.header("👑 Panel de Control")
            st.info("Bienvenida al centro de mando de La Exacta. Usa el menú lateral para gestionar tu negocio.")
        
        elif menu == "Costos (Insumos)":
            mostrar_modulo_costos()
        elif menu == "Recetas (Proyectos)":
            mostrar_modulo_recetas()
        elif menu == "Carta":
            mostrar_modulo_carta()
        elif menu == "Pedidos (Ventas)":
            mostrar_modulo_pedidos()
        elif menu == "Tracking de Pedidos":
            mostrar_modulo_tracking()
            
        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    elif rol == 'cliente':
        # --- VISTA CLIENTE / COUNTER ---
        if st.sidebar.button("⬅️ Inicio"):
            st.session_state.clear()
            st.rerun()
            
        mostrar_modulo_pedidos()
