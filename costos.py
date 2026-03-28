import streamlit as st
import pandas as pd
from database import conectar, obtener_insumos

def mostrar_modulo_costos():
    st.header("📦 Gestión de Insumos (Materia Prima)")
    
    # 1. Formulario para agregar nuevos insumos
    with st.expander("➕ Registrar Nuevo Insumo / Ingrediente", expanded=False):
        with st.form("form_insumos"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del Insumo", placeholder="Ej: Carne Res 150g")
                unidad = st.selectbox("Unidad de Medida", ["Unidades", "Kilogramos", "Gramos", "Litros", "Mililitros"])
            with col2:
                costo = st.number_input("Costo Unitario (S/.)", min_value=0.0, step=0.01, format="%.2f")
                stock = st.number_input("Stock Inicial", min_value=0.0, step=0.1)
            
            stock_min = st.number_input("Alerta Stock Mínimo", min_value=0.0, value=10.0)
            
            if st.form_submit_button("Guardar en Base de Datos"):
                if nombre:
                    try:
                        db = conectar()
                        db.table("insumos").insert({
                            "nombre": nombre,
                            "unidad_medida": unidad,
                            "costo_unitario": costo,
                            "stock_actual": stock,
                            "stock_minimo": stock_min
                        }).execute()
                        st.success(f"✅ {nombre} guardado correctamente.")
                        st.cache_data.clear() # Limpia el caché para ver el cambio
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("Por favor, ingresa un nombre para el insumo.")

    # 2. Visualización del Inventario actual
    st.subheader("📋 Lista de Precios y Stock")
    res = obtener_insumos()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Renombrar columnas para que se vea profesional
        df = df.rename(columns={
            "nombre": "Insumo",
            "unidad_medida": "Unidad",
            "costo_unitario": "Costo (S/.)",
            "stock_actual": "Stock",
            "stock_minimo": "Mínimo"
        })
        
        # Mostrar tabla (excluyendo IDs y fechas de creación para limpieza)
        columnas_ver = ["Insumo", "Unidad", "Costo (S/.)", "Stock", "Mínimo"]
        st.dataframe(df[columnas_ver], use_container_width=True)
    else:
        st.info("Aún no hay insumos registrados. Usa el formulario de arriba.")
