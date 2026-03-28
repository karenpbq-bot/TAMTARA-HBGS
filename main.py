import streamlit as st
from database import conectar
from costos import mostrar_modulo_costos
from recetas import mostrar_modulo_recetas

st.set_page_config(page_title="HBGS - Gestión", layout="wide", page_icon="🍔")

st.title("🍔 Sistema de Gestión HBGS")

# Menú lateral modular para navegar entre tus negocios
menu = st.sidebar.selectbox("Seleccione un Módulo", 
    ["Inicio", "Costos (Insumos)", "Recetas (Proyectos)", "Carta", "Pedidos", "Inventario"])

if menu == "Inicio":
    st.subheader("Panel de Control")
    st.write("Bienvenida, Karen. Aquí verás el resumen de tu hamburguesería.")
    
    col1, col2 = st.columns(2)
    col1.metric("Estado de Conexión", "São Paulo 🚀")
    col2.info("El sistema está listo para registrar insumos.")

elif menu == "Recetas (Proyectos)":
    mostrar_modulo_recetas()
