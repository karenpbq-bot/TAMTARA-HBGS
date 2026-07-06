import streamlit as st
import pandas as pd
from database import conectar
from datetime import datetime

def mostrar_modulo_tracking():
    # --- INYECCIÓN CSS PARA DISEÑO ULTRA-COMPACTO Y TARJETAS PLANAS ---
    st.markdown("""
        <style>
            .stHeading h3, .stHeading h2 {
                font-size: 1.1rem !important;
                margin-bottom: 2px !important;
                padding-bottom: 2px !important;
            }
            div[data-testid="stBlock"] div[data-testid="element-container"] .stContainer {
                padding: 4px 8px !important;
                margin-bottom: 3px !important;
                border-radius: 4px !important;
                background-color: #f9f9f9 !important;
            }
            div[data-testid="stBlock"] div[data-testid="element-container"] p {
                font-size: 0.85rem !important;
                margin: 1px 0 !important;
                line-height: 1.1 !important;
            }
            div[data-testid="stBlock"] button {
                padding: 2px 6px !important;
                font-size: 0.8rem !important;
                min-height: 24px !important;
                height: 26px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("📋 Panel de Control de Producción - La Exacta")
    db = conectar()
    
    # Extraemos todos los pedidos vigentes
    try:
        res = db.table("pedidos").select("*").order("id").execute()
        todos_los_pedidos = res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con el flujo de pedidos: {e}")
        return

    if not todos_los_pedidos:
        st.info("No hay registros de pedidos en el sistema.")
        return

    # --- LÓGICA DE FORMATEO: NÚMERO DE PEDIDO DDMM-CORRELATIVO ---
    for p in todos_los_pedidos:
        try:
            # Extraemos el día y mes de la fecha de creación en Supabase
            dt = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
            prefijo_fecha = dt.strftime("%d%m")
        except:
            prefijo_fecha = datetime.now().strftime("%d%m")
        
        # Formateamos el ID numérico como un correlativo de 3 dígitos (ej: 001, 002)
        p['codigo_exacta'] = f"{prefijo_fecha}-{int(p['id']):03d}"

    # --- BÚSQUEDA POR PALABRA CLAVE ---
    busqueda = st.text_input("🔍 Buscar pedido (Ej: Código, Cliente, Mesa, Dirección o Método de pago):", placeholder="Escribe aquí para filtrar...").strip().lower()

    # Filtrado dinámico por palabra clave
    if busqueda:
        pedidos_filtrados = []
        for p in todos_los_pedidos:
            # Campos en los que el buscador rastreará coincidencias
            cadena_auditoria = f"{p['codigo_exacta']} {p['cliente']} {p.get('destino_entrega','')} {p.get('metodo_pago','')}".lower()
            if busqueda in cadena_auditoria:
                pedidos_filtrados.append(p)
    else:
        pedidos_filtrados = todos_los_pedidos

    # Organización de Pestañas Principales
    tab_proceso, tab_entregados = st.tabs(["🔥 Pedidos en Proceso", "🏁 Historial de Entregados"])

    # --- PESTAÑA 1: TABLERO KANBAN ULTRA-COMPACTO ---
    with tab_proceso:
        pedidos_activos = [p for p in pedidos_filtrados if p.get('estado') != 'Entregado']
        
        if not pedidos_activos:
            st.success("No hay órdenes pendientes en producción con los criterios indicados.")
        else:
            en_cocina = [p for p in pedidos_activos if p.get('estado') == 'En cocina']
            listos = [p for p in pedidos_activos if p.get('estado') == 'Listo']
            despachados = [p for p in pedidos_activos if p.get('estado') == 'Despachado']

            col1, col2, col3 = st.columns(3)

            # CARRIL 1: EN COCINA
            with col1:
                st.subheader("👨‍🍳 En Cocina")
                st.divider()
                for p in en_cocina:
                    with st.container(border=True):
                        st.markdown(f"**🪪 N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})`")
                        if st.button("🔔 Listo", key=f"fwd_{p['id']}", use_container_width=True, type="primary"):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

            # CARRIL 2: LISTO EN BARRA
            with col2:
                st.subheader("🛎️ En Barra")
                st.divider()
                for p in listos:
                    with st.container(border=True):
                        st.markdown(f"**📦 N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})`")
                        c_b1, c_b2 = st.columns(2)
                        with c_b1:
                            if p['tipo_entrega'] == "Delivery":
                                if st.button("🚚 Despachar", key=f"fwd_dl_{p['id']}", use_container_width=True, type="primary"):
                                    db.table("pedidos").update({"estado": "Despachado"}).eq("id", p['id']).execute()
                                    st.rerun()
                            else:
                                if st.button("🏁 Entregar", key=f"fwd_ms_{p['id']}", use_container_width=True, type="primary"):
                                    db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                                    st.rerun()
                        with c_b2:
                            if st.button("⏪ Regresar", key=f"rev_{p['id']}", use_container_width=True):
                                db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                                st.rerun()

            # CARRIL 3: EN CAMINO
            with col3:
                st.subheader("🚚 En Camino")
                st.divider()
                for p in despachados:
                    with st.container(border=True):
                        st.markdown(f"**🏍️ N° {p['codigo_exacta']}** • {p['cliente']} `({p['destino_entrega']})`")
                        c_d1, c_d2 = st.columns(2)
                        with c_d1:
                            if st.button("🏁 Recibido", key=f"fwd_fn_{p['id']}", use_container_width=True, type="primary"):
                                db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                                st.rerun()
                        with c_d2:
                            if st.button("⏪ Regresar", key=f"rev_d_{p['id']}", use_container_width=True):
                                db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                                st.rerun()

    # --- PESTAÑA 2: HISTORIAL CON RETORNO OPERATIVO ---
    with tab_entregados:
        pedidos_entregados = [p for p in pedidos_filtrados if p.get('estado') == 'Entregado']
        
        if not pedidos_entregados:
            st.info("No hay registros de pedidos archivados que coincidan con la búsqueda.")
        else:
            st.subheader("✅ Órdenes Archivadas")
            for p in pedidos_entregados:
                with st.container(border=True):
                    ch1, ch2, ch3 = st.columns([0.2, 0.6, 0.2])
                    with ch1:
                        st.markdown(f"**🟢 N° {p['codigo_exacta']}**")
                    with ch2:
                        st.markdown(f"**Cliente:** {p['cliente']} | **Tipo:** {p['tipo_entrega']} ({p['destino_entrega']}) | **Monto:** S/. {p['monto_total']:.2f}")
                    with ch3:
                        if st.button("⏪ Devolver", key=f"ret_ent_{p['id']}", use_container_width=True):
                            estado_retorno = "Despachado" if p['tipo_entrega'] == "Delivery" else "Listo"
                            db.table("pedidos").update({"estado": estado_retorno}).eq("id", p['id']).execute()
                            st.rerun()
