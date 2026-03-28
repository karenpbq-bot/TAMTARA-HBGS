import streamlit as st
import pandas as pd
from database import conectar, obtener_insumos, obtener_productos

def mostrar_modulo_recetas():
    st.header("⚖️ Constructor de Recetas (Costeo de Proyectos)")
    
    db = conectar()
    
    # 1. Selección del Producto (El "Proyecto")
    res_productos = obtener_productos()
    if not res_productos.data:
        st.warning("⚠️ Primero debes crear productos en el módulo 'Carta'.")
        return

    nombres_productos = {p['nombre']: p['id'] for p in res_productos.data}
    producto_sel = st.selectbox("Seleccione el Producto a costear:", nombres_productos.keys())
    id_prod = nombres_productos[producto_sel]

    # 2. Formulario para añadir Insumos a la Receta
    st.subheader(f"Agregar Ingredientes a: {producto_sel}")
    res_insumos = obtener_insumos()
    
    if res_insumos.data:
        nombres_insumos = {i['nombre']: i['id'] for i in res_insumos.data}
        costos_insumos = {i['id']: i['costo_unitario'] for i in res_insumos.data}
        unidades_insumos = {i['id']: i['unidad_medida'] for i in res_insumos.data}

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            insumo_sel = st.selectbox("Seleccione Insumo:", nombres_insumos.keys())
        with col2:
            cantidad = st.number_input("Cantidad Requerida:", min_value=0.001, step=0.001, format="%.3f")
            st.caption(f"Unidad: {unidades_insumos[nombres_insumos[insumo_sel]]}")
        with col3:
            if st.button("Añadir a Receta"):
                db.table("recetas").insert({
                    "id_producto": id_prod,
                    "id_insumo": nombres_insumos[insumo_sel],
                    "cantidad_requerida": cantidad
                }).execute()
                st.success("Ingrediente añadido")
                st.rerun()

    # 3. Visualización y Cálculo del Costo Total
    st.subheader("📋 Composición y Costos Parciales")
    
    # Consulta vinculando tablas para traer nombres y costos
    receta_data = db.table("recetas").select("id, cantidad_requerida, insumos(nombre, costo_unitario)").eq("id_producto", id_prod).execute()
    
    if receta_data.data:
        filas = []
        costo_total = 0
        for r in receta_data.data:
            c_unit = float(r['insumos']['costo_unitario'])
            cant = float(r['cantidad_requerida'])
            parcial = c_unit * cant
            costo_total += parcial
            filas.append({
                "ID": r['id'],
                "Ingrediente": r['insumos']['nombre'],
                "Cantidad": cant,
                "Costo Unit.": f"S/. {c_unit:.2f}",
                "Subtotal": parcial
            })
        
        df_receta = pd.DataFrame(filas)
        st.table(df_receta[["Ingrediente", "Cantidad", "Costo Unit.", "Subtotal"]])
        
        # Resumen Financiero
        st.metric("Costo Total de Producción", f"S/. {costo_total:.2f}")
    else:
        st.info("Esta receta aún no tiene ingredientes.")
