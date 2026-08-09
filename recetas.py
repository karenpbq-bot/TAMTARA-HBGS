import streamlit as st
import pandas as pd
from database import conectar, obtener_insumos, obtener_productos

def mostrar_modulo_recetas():
    st.markdown("""
        <style>
        .report-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="report-title">⚖️ Constructor de Recetas y Costeos</p>', unsafe_allow_html=True)
    
    db = conectar()
    
    # 1. SELECCIÓN DEL TIPO DE RECETA (Nuevo Enfoque)
    tipo_receta = st.radio("¿Qué tipo de elemento vas a costear/armar?", 
                           ["Producto Final (Menú / Carta)", "Insumo Elaborado (Precocido / Salsa)"], 
                           horizontal=True)
    
    st.divider()

    id_prod = None
    id_elab = None
    elemento_sel = None

    # 2. CARGA DINÁMICA SEGÚN EL TIPO ELEGIDO
    if tipo_receta == "Producto Final (Menú / Carta)":
        res_productos = obtener_productos()
        if not res_productos.data:
            st.warning("⚠️ Primero debes crear productos en el módulo 'Carta'.")
            return
        nombres_elementos = {p['nombre']: p['id'] for p in res_productos.data}
        elemento_sel = st.selectbox("Seleccione el Producto a costear:", list(nombres_elementos.keys()))
        id_prod = nombres_elementos[elemento_sel]
        filtro_db = {"columna": "id_producto", "valor": id_prod}

    else:
        # Buscar insumos que sean de tipo "Elaborado"
        res_elaborados = db.table("insumos").select("*").eq("tipo", "Elaborado").execute()
        if not res_elaborados.data:
            st.warning("⚠️ Primero debes registrar Insumos tipo 'Elaborado' en el Catálogo del Kardex.")
            return
        nombres_elementos = {f"{p['nombre']} ({p['unidad_medida']})": p['id'] for p in res_elaborados.data}
        elemento_sel = st.selectbox("Seleccione el Elaborado a costear:", list(nombres_elementos.keys()))
        id_elab = nombres_elementos[elemento_sel]
        filtro_db = {"columna": "id_insumo_elaborado", "valor": id_elab}

    # 3. FORMULARIO PARA AÑADIR INGREDIENTES
    st.subheader(f"Agregar Ingredientes a: {elemento_sel}")
    res_insumos = obtener_insumos()
    
    if res_insumos.data:
        # Excluir el mismo elaborado de la lista para evitar "recetas infinitas"
        if id_elab:
            insumos_disponibles = [i for i in res_insumos.data if i['id'] != id_elab]
        else:
            insumos_disponibles = res_insumos.data
            
        nombres_insumos = {i['nombre']: i['id'] for i in insumos_disponibles}
        unidades_insumos = {i['id']: i['unidad_medida'] for i in insumos_disponibles}

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            insumo_sel = st.selectbox("Seleccione Ingrediente:", list(nombres_insumos.keys()))
        with col2:
            cantidad = st.number_input("Cantidad Requerida:", min_value=0.001, step=0.001, format="%.3f")
            st.caption(f"Unidad: {unidades_insumos[nombres_insumos[insumo_sel]]}")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True) # Espaciado
            if st.button("➕ Añadir a Receta", type="primary", use_container_width=True):
                # Armamos el payload dinámico dependiendo de qué estamos costeando
                payload_receta = {
                    "id_insumo": nombres_insumos[insumo_sel],
                    "cantidad_requerida": cantidad
                }
                
                if id_prod: payload_receta["id_producto"] = id_prod
                if id_elab: payload_receta["id_insumo_elaborado"] = id_elab
                
                db.table("recetas").insert(payload_receta).execute()
                st.success("Ingrediente añadido")
                st.rerun()

    # 4. VISUALIZACIÓN DE LA RECETA ACTUAL
    st.subheader("📋 Composición y Costos Parciales")
    
    # Consulta a base de datos usando el filtro dinámico y resolviendo la ambigüedad de la Foreign Key (!id_insumo)
    receta_data = db.table("recetas").select("id, cantidad_requerida, insumos!id_insumo(nombre, costo_unitario, unidad_medida)").eq(filtro_db["columna"], filtro_db["valor"]).execute()
    
    if receta_data.data:
        filas = []
        costo_total = 0
        for r in receta_data.data:
            c_unit = float(r['insumos']['costo_unitario'] or 0.0)
            cant = float(r['cantidad_requerida'])
            parcial = c_unit * cant
            costo_total += parcial
            filas.append({
                "ID": r['id'],
                "Ingrediente": f"{r['insumos']['nombre']} ({r['insumos']['unidad_medida']})",
                "Cantidad": cant,
                "Costo Unit.": f"S/. {c_unit:.2f}",
                "Subtotal": parcial
            })
        
        df_receta = pd.DataFrame(filas)
        
        # Opciones para eliminar un ingrediente
        c_t1, c_t2 = st.columns([3, 1])
        with c_t1:
            st.dataframe(df_receta[["Ingrediente", "Cantidad", "Costo Unit.", "Subtotal"]], use_container_width=True)
        with c_t2:
            st.write("Eliminar Ingrediente:")
            for index, row in df_receta.iterrows():
                if st.button(f"🗑️ Quitar", key=f"del_{row['ID']}", use_container_width=True):
                    db.table("recetas").delete().eq("id", row['ID']).execute()
                    st.rerun()
        
        # Resumen Financiero
        st.metric("Costo Total de Producción (Base)", f"S/. {costo_total:.2f}")
    else:
        st.info("Esta receta aún no tiene ingredientes vinculados.")
