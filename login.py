import streamlit as st

def login_manager():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
        st.session_state['rol'] = None

    if not st.session_state['autenticado']:
        st.subheader("🍕 Bienvenido a HBGS")
        col1, col2 = st.columns(2)
        
        if col1.button("🛒 Hacer un Pedido (Cliente)", use_container_width=True):
            st.session_state['autenticado'] = True
            st.session_state['rol'] = 'cliente'
            st.rerun()
            
        if col2.button("🔐 Acceso Administrador", use_container_width=True):
            password = st.text_input("Contraseña", type="password")
            if password == "HBGS2026": # Puedes cambiar esta clave después
                st.session_state['autenticado'] = True
                st.session_state['rol'] = 'admin'
                st.success("Acceso concedido")
                st.rerun()
    
    return st.session_state['autenticado'], st.session_state['rol']
