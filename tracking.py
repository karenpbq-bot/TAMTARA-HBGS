import streamlit as st
import pandas as pd
from database import conectar

def mostrar_modulo_tracking():
    st.header("📋 Panel de Control de Producción - La Exacta")
    db = conectar()
    
    # Extraemos todos los pedidos para procesarlos en pestañas separadas
    try:
        res = db.table("pedidos").select("*").order("id").execute()
        todos_los_pedidos = res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con el flujo de pedidos: {e}")
        return

    if not todos_los_pedidos:
        st.info("No hay registros de pedidos en el sistema.")
        return

    # Organización de Pestañas Principales
    tab_proceso, tab_entregados = st.tabs(["🔥 Pedidos en Proceso", "🏁 Historial de Entregados"])

    # --- PESTAÑA 1: PEDIDOS ACTIVOS EN COLO RESUMIDA ---
    with tab_proceso:
        pedidos_activos = [p for p in todos_los_pedidos if p.get('estado') != 'Entregado']
        
        if not pedidos_activos:
            st.success("¡Excelente! No hay órdenes pendientes en producción.")
        else:
            en_cocina = [p for p in pedidos_activos if p.get('estado') == 'En cocina']
            listos = [p for p in pedidos_activos if p.get('estado') == 'Listo']
            despachados = [p for p in pedidos_activos if p.get('estado') == 'Despachado']

            col1, col2, col3 = st.columns(3)

            # CARRIL: EN COCINA
            with col1:
                st.subheader("👨‍🍳 En Cocina")
                st.divider()
                for p in en_cocina:
                    with st.container(border=True):
                        # VISTA COMPACTA: Solo ID, Cliente y Destino
                        st.markdown(f"### 🪪 N° {p['id']}")
                        st.write(f"**{p['cliente']}** ({p['destino_entrega']})")
                        
                        if st.button("🔔 Listo", key=f"fwd_{p['id']}", use_container_width=True, type="primary"):
                            db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                            st.rerun()

            # CARRIL: LISTO EN BARRA
            with col2:
                st.subheader("🛎️ Listo en Barra")
                st.divider()
                for p in listos:
                    with st.container(border=True):
                        st.markdown(f"### 📦 N° {p['id']}")
                        st.write(f"**{p['cliente']}** ({p['destino_entrega']})")
                        
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
                            # BOTÓN DE REVERSA POR ERROR
                            if st.button("⏪ Regresar", key=f"rev_{p['id']}", use_container_width=True):
                                db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                                st.rerun()

            # CARRIL: EN CAMINO (LOGÍSTICA DELIVERY)
            with col3:
                st.subheader("🛵 En Camino")
                st.divider()
                for p in despachados:
                    with st.container(border=True):
                        st.markdown(f"### 🏍️ N° {p['id']}")
                        st.write(f"**{p['cliente']}** ({p['destino_entrega']})")
                        
                        c_d1, c_d2 = st.columns(2)
                        with c_d1:
                            if st.button("🏁 Recibido", key=f"fwd_fn_{p['id']}", use_container_width=True, type="primary"):
                                db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                                st.rerun()
                        with c_d2:
                            # BOTÓN DE REVERSA POR ERROR
                            if st.button("⏪ Regresar", key=f"rev_d_{p['id']}", use_container_width=True):
                                db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                                st.rerun()

    # --- PESTAÑA 2: HISTORIAL COMPACTO DE ENTREGADOS ---
    with tab_entregados:
        pedidos_entregados = [p for p in todos_los_pedidos if p.get('estado') == 'Entregado']
        
        if not pedidos_entregados:
            st.info("Aún no se registran pedidos entregados en el turno actual.")
        else:
            st.subheader("✅ Órdenes Archivadas")
            # Tabla ejecutiva rápida para auditoría
            data_tabla = []
            for p in pedidos_entregados:
                data_tabla.append({
                    "N° Pedido": p['id'],
                    "Cliente": p['cliente'],
                    "Entrega": p['tipo_entrega'],
                    "Destino/Mesa": p['destino_entrega'],
                    "Pago": p['metodo_pago'],
                    "Monto Cobrado": f"S/. {p['monto_total']:.2f}"
                })
            
            df_entregados = pd.DataFrame(data_tabla)
            st.dataframe(df_entregados, use_container_width=True, hide_index=True)
