import streamlit as st
import pandas as pd
from database import conectar, obtener_productos
from datetime import datetime

def mostrar_modulo_comandas_pendientes():
    st.markdown("### 📝 Pedidos Generados (Pendientes de Pago / Consumo Abierto)")
    db = conectar()

    tab_lista, tab_nuevo = st.tabs(["📋 Listado de Pendientes", "➕ Nuevo Pedido Abierto"])

    with tab_lista:
        try:
            # Filtramos únicamente los pedidos en estado 'Generado'
            res = db.table("pedidos").select("*").eq("estado", "Generado").order("id", desc=True).execute()
            pendientes = res.data if res.data else []

            if not pendientes:
                st.info("✨ No hay pedidos generados pendientes de pago actualmente.")
            else:
                for p in pendientes:
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 1.5])
                        
                        with c1:
                            st.markdown(f"**Cliente:** {p.get('cliente')}")
                            st.caption(f"Ubicación: **{p.get('destino_entrega', 'Local')}** | Fecha: {p.get('created_at', '')[:16]}")
                        
                        with c2:
                            total_parcial = float(p.get('monto_total', 0.0))
                            st.markdown(f"**Total Parcial:**\n### S/. {total_parcial:.2f}")
                        
                        with c3:
                            # Botón para ir al módulo de venta/caja o procesar cobro rápido
                            if st.button("💳 Proceder al Pago", key=f"cobrar_{p['id']}", type="primary", use_container_width=True):
                                # Al pagar, lo pasamos al flujo normal del Kanban
                                db.table("pedidos").update({"estado": "En cocina"}).eq("id", p['id']).execute()
                                st.success(f"✅ Pedido de {p.get('cliente')} enviado a cocina y caja.")
                                st.rerun()

                        with c4:
                            if st.button("🗑️ Anular", key=f"del_{p['id']}", use_container_width=True):
                                db.table("pedidos").delete().eq("id", p['id']).execute()
                                st.rerun()

                        # Desglose de ítems consumidos
                        items = p.get('items', [])
                        if items:
                            with st.expander("Ver productos en la comanda"):
                                for item in items:
                                    p_ad = sum(float(a['precio']) for a in item.get('adicionales', []))
                                    sub = (item['precio_base'] + p_ad) * item['cantidad']
                                    st.markdown(f"- **{item['cantidad']}x** {item['nombre']} — S/. {sub:.2f}")
        except Exception as e:
            st.error(f"Error al cargar pedidos pendientes: {e}")

    with tab_nuevo:
        with st.form("form_nuevo_generado"):
            st.markdown("#### ⚡ Registro de Pedido sin Pago Inmediato")
            c_m1, c_m2 = st.columns(2)
            nombre_cli = c_m1.text_input("Nombre del Cliente:")
            ubicacion = c_m2.text_input("Mesa / Destino (Ej: Mesa 2, Barra):")

            if st.form_submit_button("🚀 Registrar Pedido Generado", type="primary"):
                if nombre_cli.strip() and ubicacion.strip():
                    nuevo_payload = {
                        "cliente": nombre_cli.strip().upper(),
                        "tipo_entrega": "Mesa",
                        "destino_entrega": ubicacion.strip().upper(),
                        "telefono_contacto": "",
                        "items": [],
                        "metodo_pago": "Pendiente",
                        "monto_total": 0.0,
                        "estado": "Generado",
                        "pedido_cerrado": "No",
                        "cortesia": "No",
                        "codigo_exacta": f"GEN-{datetime.now().strftime('%H%M%S')}"
                    }
                    db.table("pedidos").insert(nuevo_payload).execute()
                    st.success("✅ Pedido generado guardado con éxito. Está pendiente de pago y oculto del Kanban.")
                    st.rerun()
                else:
                    st.warning("⚠️ Debe completar el nombre del cliente y la ubicación.")
