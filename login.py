import streamlit as st

def login_manager():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
        st.session_state['rol'] = None

    if not st.session_state['autenticado']:
        # 1. Título y Reseña Central
        st.title("🍔 Bienvenido a HBGS")
        
        st.markdown(f"""
        <div style="font-style: italic; border-left: 4px solid #ff4b4b; padding-left: 15px; margin: 30px 0; color: #555; font-size: 1.2em;">
            "HBGS nació con la intención de ofrecer una experiencia culinaria muy personal 
            y surgió de la pasión por la comida simple que es capaz de llenar el alma."
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Botón de Pedido Grande y Centrado
        if st.button("🛒 Hacer un pedido", use_container_width=True, type="primary"):
            st.session_state['autenticado'] = True
            st.session_state['rol'] = 'cliente'
            st.rerun()

        # 3. Espaciado para empujar el candado hacia abajo
        for _ in range(10): st.write("") 

        # 4. Candado en la esquina inferior (usando columnas para alinearlo a la derecha)
        col_espacio, col_candado = st.columns([0.9, 0.1])
        with col_candado:
            with st.popover("🔐", help="Admin"):
                password = st.text_input("Clave", type="password")
                if st.button("Entrar"):
                    if password == "HBGS2026":
                        st.session_state['autenticado'] = True
                        st.session_state['rol'] = 'admin'
                        st.rerun()
                    else:
                        st.error("Incorrecto")
    
    return st.session_state['autenticado'], st.session_state['rol']
