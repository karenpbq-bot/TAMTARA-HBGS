import streamlit as st
import os
from database import conectar
from login import login_manager
from pedidos import mostrar_modulo_pedidos
from costos import mostrar_modulo_costos
from recetas import mostrar_modulo_recetas
from carta import mostrar_modulo_carta

# --- CONFIGURACIÓN DE IDENTIDAD VISUAL EN LA NUBE ---
# Apuntamos a la URL directa del logo subido en tu repositorio de GitHub
URL_LOGO_LA_EXACTA = "https://raw.githubusercontent.com/tamtara-hbgs/main/Logo.png"

# 1. Configuración de página (MODIFICADO: Tu logo real en la pestaña del navegador)
st.set_page_config(
    page_title="La Exacta - Hamburguesería",
    layout="centered", 
    initial_sidebar_state="collapsed", 
    page_icon=URL_LOGO_LA_EXACTA  # <-- Reemplaza el tronco por la URL de la imagen
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
            st.info("Bienvenida al centro de mando de La Exacta. Usa el menú lateral para gestionar tu negocio.")
        
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
