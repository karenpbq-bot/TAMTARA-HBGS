import streamlit as st
import os

def login_manager():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
        st.session_state['rol'] = None

    if not st.session_state['autenticado']:
        # --- CARGA DEL LOGO CORPORATIVO DE LA EXACTA (REDUCIDO 40%) ---
        directorio_actual = os.path.dirname(__file__)
        ruta_logo_exacta = os.path.join(directorio_actual, ".streamlit", "static", "logo.png")

        # Creamos columnas para centrar y reducir el tamaño visual del logo al 60%
        c_izq, c_centro, c_der = st.columns([1, 1.2, 1])
        with c_centro:
            if os.path.exists(ruta_logo_exacta):
                st.image(ruta_logo_exacta, width=220)  # Ancho controlado para hacerlo más pequeño
            else:
                st.title("La Exacta")
        
        st.markdown(f"""
        <div style="font-style: italic; border-left: 4px solid #ff4b4b; padding-left: 15px; margin: 30px 0; color: #555; font-size: 1.2em;">
            "La Exacta nació con la intención de ofrecer una experiencia culinaria muy personal 
            y surgió de la pasión por la comida simple que es capaz de llenar el alma."
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🛒 Hacer un pedido", use_container_width=True, type="primary"):
            st.session_state['autenticado'] = True
            st.session_state['rol'] = 'cliente'
            st.rerun()

        for _ in range(10): st.write("") 

        col_espacio, col_candado = st.columns([0.9, 0.1])
        with col_candado:
            # Acceso directo como administrador al presionar el icono del candado
            if st.button("🔐", help="Acceso Admin Directo", use_container_width=True):
                st.session_state['autenticado'] = True
                st.session_state['rol'] = 'admin'
                st.rerun()
    
    return st.session_state['autenticado'], st.session_state['rol']
