import streamlit as st
import pandas as pd
from database import conectar

def mostrar_modulo_tracking():
    st.header("📋 Tracking de Pedidos en Tiempo Real - La Exacta")
    db = conectar()
    
    # Traemos los pedidos no culminados
    try:
        res = db.table("pedidos").select("*").not_.eq("estado", "Entregado").order("id").execute()
        pedidos = res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con el flujo de pedidos: {e}")
        return

    if not pedidos:
        st.info("🎉 ¡Todos los pedidos del counter han sido despachados y entregados!")
        return

    # Clasificamos según la nueva lógica relacional
    en_cocina = [p for p in pedidos if p.get('estado') == 'En cocina']
    listos = [p for p in pedidos if p.get('estado') == 'Listo']
    despachados = [p for p in pedidos if p.get('estado') == 'Despachado']

    # Visualización Kanban de tres carriles adaptativa
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔥 En Cocina")
        st.divider()
        for p in en_cocina:
            with st.container(border=True):
                st.markdown(f"#### 🪪 Pedido N° {p['id']}")
                st.write(f"**Cliente:** {p['cliente']}")
                st.write(f"**Tipo:** {p['tipo_entrega']} ({p['destino_entrega']})")
                for item in p.get('items', []):
                    st.caption(f"• {item['cantidad']}x {item['nombre']}")
                    if item.get('adicionales'):
                        st.caption(f"  └ {', '.join([a['nombre'] for a in item['adicionales']])}")
                
                if st.button("🔔 Pasar a Barra", key=f"bar_{p['id']}", use_container_width=True, type="primary"):
                    db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                    st.rerun()

    with col2:
        st.subheader("✅ Listos en Barra")
        st.divider()
        for p in listos:
            with st.container(border=True):
                st.markdown(f"#### 📦 Pedido N° {p['id']}")
                st.write(f"**Cliente:** {p['cliente']}")
                st.write(f"**Ubicación:** {p['destino_entrega']}")
                
                if p['tipo_entrega'] == "Delivery":
                    if st.button("🚚 Despachar con Motorizado", key=f"desp_{p['id']}", use_container_width=True, type="primary"):
                        db.table("pedidos").update({"estado": "Despachado"}).eq("id", p['id']).execute()
                        st.rerun()
                else:
                    if st.button("🏁 Entregar al Cliente", key=f"ent_m_{p['id']}", use_container_width=True):
                        db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                        st.rerun()

    with col3:
        st.subheader("🚚 En Camino")
        st.divider()
        for p in despachados:
            with st.container(border=True):
                st.markdown(f"#### 🏍️ Pedido N° {p['id']} (Ruta)")
                st.write(f"**Cliente:** {p['cliente']}")
                st.write(f"**Dirección:** {p['destino_entrega']}")
                st.write(f"**Celular:** {p.get('telefono_contacto', 'N/A')}")
                
                if st.button("🏁 Confirmar Recepción", key=f"fin_{p['id']}", use_container_width=True):
                    db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                    st.rerun()
