import streamlit as st
import pandas as pd
from database import conectar, obtener_insumos

def mostrar_modulo_costos():
    st.header("📦 Gestión de Insumos (Materia Prima)")
    db = conectar()
    
    # 1. FORMULARIO DE REGISTRO
    with st.expander("➕ Registrar Nuevo Insumo", expanded=False):
        with st.form("form_nuevo_insumo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nombre del Insumo")
                und = st.selectbox("Unidad", ["Unidades", "Kilogramos", "Gramos", "Litros"])
            with col2:
                costo = st.number_input("Costo Unitario (S/.)", min_value=0.0, step=0.01)
                stock = st.number_input("Stock Actual", min_value=0.0)
            
            if st.form_submit_button("Guardar Insumo"):
                db.table("insumos").insert({
                    "nombre": nom, "unidad_medida": und, 
                    "costo_unitario": costo, "stock_actual": stock
                }).execute()
                st.success("✅ Insumo guardado")
                st.cache_data.clear()
                st.rerun()

    # 2. TABLA DE GESTIÓN (EDITAR / ELIMINAR)
    st.subheader("📋 Lista de Insumos")
    res = obtener_insumos()
    
    if res.data:
        for i in res.data:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{i['nombre']}** ({i['unidad_medida']})")
                c2.write(f"S/. {i['costo_unitario']:.2f}")
                c3.write(f"Stock: {i['stock_actual']}")
                
                # Acciones
                if c4.button("🗑️", key=f"del_ins_{i['id']}"):
                    db.table("insumos").delete().eq("id", i['id']).execute()
                    st.cache_data.clear()
                    st.rerun()
                
                # Formulario rápido de edición de precio/stock
                with st.expander(f"Editar {i['nombre']}"):
                    with st.form(f"edit_ins_{i['id']}"):
                        nuevo_p = st.number_input("Nuevo Precio", value=float(i['costo_unitario']))
                        nuevo_s = st.number_input("Nuevo Stock", value=float(i['stock_actual']))
                        if st.form_submit_button("Actualizar"):
                            db.table("insumos").update({
                                "costo_unitario": nuevo_p, 
                                "stock_actual": nuevo_s
                            }).eq("id", i['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
    else:
        st.info("No hay insumos registrados.")
