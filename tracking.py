import streamlit as st
import pandas as pd
from database import conectar

def mostrar_modulo_traking():
    st.header("📋 Tracking de Pedidos - La Exacta")
    db = conectar()
    
    # 1. Consulta en tiempo real a la base de datos de Supabase
    try:
        res = db.table("pedidos").select("*").not_.eq("estado", "Entregado").order("id").execute()
        pedidos = res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con el flujo de pedidos: {e}")
        pedidos = []

    if not pedidos:
        st.info("🎉 ¡No hay pedidos pendientes en producción! Todo entregado.")
        return

    # Clasificación por estados operativos
    en_cocina = [p for p in pedidos if p.get('estado') == 'En cocina']
    listos = [p for p in pedidos if p.get('estado') == 'Listo']

    # --- DISEÑO DE PANTALLA DIVIDIDA EN COLUMNAS (Estilo KANBAN) ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 En Cocina")
        st.caption("Pedidos recibidos en espera o preparación")
        st.divider()
        
        for p in en_cocina:
            with st.container(border=True):
                st.markdown(f"### 🪪 Pedido N° {p['id']}")
                st.write(f"**Cliente:** {p.get('cliente', 'No registrado')}")
                st.write(f"**Destino:** {p.get('destino_entrega', 'Mesa / Llevar')}")
                
                # Despliegue de los productos del pedido guardados en JSON
                st.write("**Detalle:**")
                for item in p.get('items', []):
                    st.write(f"- {item['cantidad']}x {item['nombre']}")
                    if item.get('adicionales'):
                        ads = ", ".join([a['nombre'] for a in item['adicionales']])
                        st.caption(f"  └ Adicionales: {ads}")
                
                # Botón de transición de estado
                if st.button("🔔 Listo para Despacho", key=f"ready_{p['id']}", use_container_width=True, type="primary"):
                    db.table("pedidos").update({"estado": "Listo"}).eq("id", p['id']).execute()
                    st.cache_data.clear()
                    st.rerun()

    with col2:
        st.subheader("✅ Listos para Entregar")
        st.caption("Pedidos listos en barra esperando despacho")
        st.divider()
        
        for p in listos:
            with st.container(border=True):
                st.markdown(f"### 📦 Pedido N° {p['id']}")
                st.write(f"**Cliente:** {p.get('cliente', 'No registrado')}")
                st.write(f"**Destino:** {p.get('destino_entrega', 'Mesa / Llevar')}")
                
                if st.button("🏁 Entregado y Archivar", key=f"deliver_{p['id']}", use_container_width=True):
                    db.table("pedidos").update({"estado": "Entregado"}).eq("id", p['id']).execute()
                    st.cache_data.clear()
                    st.rerun()
