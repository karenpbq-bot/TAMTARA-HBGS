import streamlit as st
import os
from database import conectar
from login import login_manager
from pedidos import mostrar_modulo_pedidos
from costos import mostrar_modulo_costos
from recetas import mostrar_modulo_recetas
from carta import mostrar_modulo_carta

# --- CONTROL LÓGICO DE LOGO CORPORATIVO ---
directorio_actual = os.path.dirname(__file__)
ruta_logo_exacta = os.path.join(directorio_actual, "Logo_La_Exacta_1.jpg")

# 1. Configuración de página (MODIFICADO: )
st.set_page_config(
    page_title="La Exacta",
    layout="centered", 
    initial_sidebar_state="collapsed", 
    page_icon=ruta_logo_exacta if os.path.exists(ruta_logo_exacta) else "Logo_La_Exacta_1.jpg"
)

# 2. Ejecutar el gestor de acceso
autenticado, rol = login_manager()

# 3. Lógica de visualización post-login
if autenticado:
    if rol == 'admin':
        # --- VISTA KAREN (ADMIN) ---
        st.sidebar.title("🎛️ Panel Admin")
        menu = st.sidebar.selectbox("Seleccione un Módulo", 
            ["Inicio", "Costos (Insumos)", "Recetas (Proyectos)", "Carta", "Pedidos (Ventas)"])
        
        # AQUÍ ES DONDE LIMPIAMOS EL CONTENIDO CENTRAL
        if menu == "Inicio":
            st.header("👑 Panel de Control")
            st.info("Bienvenida al centro de mando de HBGS. Usa el menú lateral para gestionar tu negocio.")
        
        elif menu == "Costos (Insumos)":
            mostrar_modulo_costos()
        elif menu == "Recetas (Proyectos)":
            mostrar_modulo_recetas()
        elif menu == "Carta":
            mostrar_modulo_carta()
        elif menu == "Pedidos (Ventas)":
            mostrar_modulo_pedidos()
            
        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    elif rol == 'cliente':
        # --- VISTA CLIENTE (DELIVERY) ---
        # Botón discreto para volver
        if st.sidebar.button("⬅️ Inicio"):
            st.session_state.clear()
            st.rerun()
            
        # Solo mostramos el catálogo de pedidos
        mostrar_modulo_pedidos()
