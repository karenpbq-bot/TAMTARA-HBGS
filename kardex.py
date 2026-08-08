import streamlit as st
import pandas as pd
from datetime import datetime
from database import conectar

def mostrar_modulo_kardex():
    st.markdown("""
        <style>
        .report-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="report-title">📦 Kardex y Control de Inventarios</p>', unsafe_allow_html=True)
    
    tab_catalogo, tab_ingresos, tab_produccion, tab_reporte = st.tabs([
        "📖 Catálogo de Insumos", 
        "📥 Ingresos por Compra", 
        "🍳 Producción de Elaborados", 
        "📊 Stock en Tiempo Real"
    ])
    
    db = conectar()

    # ==========================================
    # PESTAÑA 1: CATÁLOGO MAESTRO (Reemplaza a costos.py)
    # ==========================================
    with tab_catalogo:
        st.subheader("Registrar Nuevo Insumo o Elaborado")
        with st.form("form_nuevo_insumo", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre del Insumo / Precocido (*):")
            tipo = c2.selectbox("Clasificación:", ["Materia Prima", "Elaborado"])
            und = c3.selectbox("Unidad de Medida:", ["Unidades", "Kilogramos", "Gramos", "Litros", "Mililitros"])
            
            if st.form_submit_button("💾 Guardar en Catálogo", type="primary"):
                if nom.strip():
                    db.table("insumos").insert({
                        "nombre": nom.strip(),
                        "tipo": tipo,
                        "unidad_medida": und,
                        "costo_unitario": 0.0 # El costo real se calculará en el Kardex
                    }).execute()
                    st.success(f"✅ {nom} registrado en el catálogo.")
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio.")

    # ==========================================
    # PESTAÑA 2: INGRESOS POR COMPRA (Abastecimiento)
    # ==========================================
    with tab_ingresos:
        st.subheader("Registrar Compra de Materia Prima")
        res_insumos = db.table("insumos").select("*").eq("tipo", "Materia Prima").order("nombre").execute()
        
        if res_insumos.data:
            insumos_mp = {f"{i['nombre']} ({i['unidad_medida']})": i['id'] for i in res_insumos.data}
            
            with st.form("form_compras", clear_on_submit=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                sel_mp = c1.selectbox("Seleccione Insumo Comprado:", list(insumos_mp.keys()))
                cant_compra = c2.number_input("Cantidad Ingresada:", min_value=0.01, step=1.0)
                costo_total_compra = c3.number_input("Costo Total (S/.):", min_value=0.0, step=1.0)
                ref_compra = st.text_input("Referencia (N° Boleta/Factura):")
                
                if st.form_submit_button("📥 Registrar Ingreso a Kardex", type="primary"):
                    costo_unitario = costo_total_compra / cant_compra if cant_compra > 0 else 0
                    id_insumo = insumos_mp[sel_mp]
                    
                    # Insertar movimiento positivo en el Kardex
                    db.table("kardex_movimientos").insert({
                        "insumo_id": id_insumo,
                        "tipo_movimiento": "Ingreso Compra",
                        "cantidad": cant_compra,
                        "costo_unitario": costo_unitario,
                        "referencia": ref_compra
                    }).execute()
                    st.success("Ingreso registrado correctamente en el inventario.")
                    st.rerun()
        else:
            st.info("Primero registre Materia Prima en el Catálogo.")

    # ==========================================
    # PESTAÑA 3: PRODUCCIÓN DE ELABORADOS
    # ==========================================
    with tab_produccion:
        st.subheader("Declarar Preparación de Precocidos / Salsas")
        res_elaborados = db.table("insumos").select("*").eq("tipo", "Elaborado").order("nombre").execute()
        
        if res_elaborados.data:
            insumos_elab = {f"{i['nombre']} ({i['unidad_medida']})": i['id'] for i in res_elaborados.data}
            
            with st.form("form_produccion", clear_on_submit=True):
                c1, c2 = st.columns([2, 1])
                sel_elab = c1.selectbox("Seleccione Elaborado Producido:", list(insumos_elab.keys()))
                cant_prod = c2.number_input("Cantidad Producida:", min_value=0.01, step=1.0)
                ref_prod = st.text_input("Responsable / Lote de Producción:")
                
                if st.form_submit_button("🍳 Generar Stock y Descontar Receta", type="primary"):
                    id_elab = insumos_elab[sel_elab]
                    
                    # 1. Traer la receta de este elaborado
                    res_receta = db.table("recetas").select("*").eq("id_insumo_elaborado", id_elab).execute()
                    
                    if not res_receta.data:
                        st.error("⚠️ Este elaborado no tiene una receta vinculada. Vaya al módulo Recetas para configurarlo.")
                    else:
                        # 2. Descontar la materia prima (Movimientos negativos)
                        movimientos = []
                        for ingrediente in res_receta.data:
                            cant_a_descontar = float(ingrediente['cantidad_requerida']) * cant_prod
                            movimientos.append({
                                "insumo_id": ingrediente['id_insumo'],
                                "tipo_movimiento": "Salida Producción",
                                "cantidad": -cant_a_descontar, # NEGATIVO
                                "costo_unitario": 0, # El costo se asume del promedio
                                "referencia": f"Prep: {sel_elab}"
                            })
                        
                        # 3. Ingresar el producto elaborado al stock (Movimiento positivo)
                        movimientos.append({
                            "insumo_id": id_elab,
                            "tipo_movimiento": "Ingreso Producción",
                            "cantidad": cant_prod, # POSITIVO
                            "costo_unitario": 0, 
                            "referencia": ref_prod
                        })
                        
                        # Ejecutar transacción masiva
                        db.table("kardex_movimientos").insert(movimientos).execute()
                        st.success("✅ Producción registrada: Stock de elaborado generado e insumos descontados.")
                        st.rerun()
        else:
            st.info("No hay productos elaborados registrados en el catálogo.")

    # ==========================================
    # PESTAÑA 4: STOCK EN TIEMPO REAL
    # ==========================================
    with tab_reporte:
        st.subheader("Niveles de Inventario Actuales")
        
        # Obtenemos todos los insumos y cruzamos con la suma del kardex
        insumos = db.table("insumos").select("id, nombre, tipo, unidad_medida").execute().data
        movimientos = db.table("kardex_movimientos").select("insumo_id, cantidad").execute().data
        
        if insumos and movimientos:
            df_mov = pd.DataFrame(movimientos)
            stock_agrupado = df_mov.groupby('insumo_id')['cantidad'].sum().reset_index()
            
            df_insumos = pd.DataFrame(insumos)
            df_final = pd.merge(df_insumos, stock_agrupado, left_on='id', right_on='insumo_id', how='left').fillna(0)
            
            df_final = df_final.rename(columns={
                "nombre": "Insumo / Producto", 
                "tipo": "Clasificación",
                "unidad_medida": "Unidad",
                "cantidad": "Stock Actual"
            })
            
            # Formateo visual
            df_final["Stock Actual"] = df_final["Stock Actual"].map(lambda x: f"{x:,.2f}")
            
            st.dataframe(df_final[["Insumo / Producto", "Clasificación", "Stock Actual", "Unidad"]], use_container_width=True, hide_index=True)
        else:
            st.info("No hay movimientos registrados en el Kardex aún.")
