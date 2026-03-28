import streamlit as st

def login_manager():
    # Inicializar estados de sesión
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
        st.session_state['rol'] = None

    # Si no está autenticado, mostramos la pantalla de inicio
    if not st.session_state['autenticado']:
        # 1. Encabezado Principal
        st.title("🍕 Bienvenido a HBGS")
        
        # 2. Reseña de la Empresa (Estilo Cita Culinaria)
        st.markdown(f"""
        <div style="font-style: italic; border-left: 4px solid #ff4b4b; padding-left: 15px; margin: 20px 0; color: #555;">
            "HBGS nació con la intención de ofrecer una experiencia culinaria muy personal 
            y surgió de la pasión por la comida simple que es capaz de llenar el alma."
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # 3. Botón de Pedido (Protagonista) y Candado (Discreto)
        col_pedido, col_admin = st.columns([0.9, 0.1])
        
        with col_pedido:
            if st.button("🛒 Hacer un pedido", use_container_width=True, type="primary"):
                st.session_state['autenticado'] = True
                st.session_state['rol'] = 'cliente'
                st.rerun()
        
        with col_admin:
            # Usamos un popover para que el formulario de clave no ocupe espacio
            with st.popover("🔐", help="Acceso restringido"):
                st.caption("Administración")
                password = st.text_input("Clave", type="password", key="admin_pwd")
                if st.button("Entrar", key="btn_login_admin"):
                    if password == "HBGS2026":
                        st.session_state['autenticado'] = True
                        st.session_state['rol'] = 'admin'
                        st.rerun()
                    else:
                        st.error("Incorrecto")
    
    return st.session_state['autenticado'], st.session_state['rol']
