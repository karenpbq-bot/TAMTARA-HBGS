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
                if not nom.strip():
                    st.error("⚠️ El nombre del insumo es obligatorio.")
                else:
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
    
    if res and res.data:
        for i in res.data:
            # Validación segura de ID para evitar fallos si el registro está incompleto
            insumo_id = i.get('id')
            if not insumo_id:
                continue
                
            nombre = i.get('nombre', 'Sin nombre')
            unidad = i.get('unidad_medida', 'Unidades')
            costo_u = float(i.get('costo_unitario', 0.0))
            stock_a = float(i.get('stock_actual', 0.0))

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{nombre}** ({unidad})")
                c2.write(f"S/. {costo_u:.2f}")
                c3.write(f"Stock: {stock_a}")
                
                # Acciones (Borrar)
                if c4.button("🗑️", key=f"del_ins_{insumo_id}"):
                    db.table("insumos").delete().eq("id", insumo_id).execute()
                    st.cache_data.clear()
                    st.rerun()
                
                # Formulario rápido de edición de precio/stock protegido contra KeyErrors
                with st.expander(f"Editar {nombre}"):
                    with st.form(f"edit_ins_{insumo_id}"):
                        nuevo_p = st.number_input("Nuevo Precio", value=costo_u, key=f"p_{insumo_id}")
                        nuevo_s = st.number_input("Nuevo Stock", value=stock_a, key=f"s_{insumo_id}")
                        if st.form_submit_button("Actualizar"):
                            db.table("insumos").update({
                                "costo_unitario": nuevo_p, 
                                "stock_actual": nuevo_s
                            }).eq("id", insumo_id).execute()
                            st.cache_data.clear()
                            st.rerun()
    else:
        st.info("No hay insumos registrados.")
