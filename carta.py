import streamlit as st
import pandas as pd
from database import conectar, obtener_productos, subir_imagen_producto

def mostrar_modulo_carta():
    st.header("📋 Gestión de la Carta (Productos)")
    db = conectar()
    
    # --- 1. FORMULARIO DE CREACIÓN ---
    with st.expander("➕ Registrar Nuevo Producto", expanded=False):
        with st.form("form_nuevo_producto", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                nombre = st.text_input("Nombre del Producto")
                desc = st.text_area("Descripción")
            with col2:
                precio = st.number_input("Precio Venta (S/.)", min_value=0.0, step=0.50)
                cat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos", "Promos"])
            
            foto = st.file_uploader("Foto del producto", type=["jpg", "png", "jpeg"], key="nueva_foto")
            
            if st.form_submit_button("Guardar Producto"):
                if nombre and precio > 0:
                    url_foto = None
                    if foto:
                        nombre_archivo = f"prod_{nombre.lower().replace(' ', '_')}_{foto.name}"
                        url_foto = subir_imagen_producto(foto, nombre_archivo)
                    
                    db.table("productos").insert({
                        "nombre": nombre, "descripcion": desc, "precio_venta": precio, 
                        "categoria": cat, "imagen_url": url_foto
                    }).execute()
                    st.success("✅ Producto creado")
                    st.cache_data.clear()
                    st.rerun()

    # --- 2. GALERÍA Y GESTIÓN DE PRODUCTOS ---
    st.subheader("🖼️ Productos en la Carta")
    res = obtener_productos()
    
    if res.data:
        for p in res.data:
            with st.container(border=True):
                col_img, col_info, col_btns = st.columns([1, 2, 1])
                
                # Imagen
                with col_img:
                    if p['imagen_url']:
                        st.image(p['imagen_url'], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                
                # Información actual
                with col_info:
                    st.write(f"### {p['nombre']}")
                    st.write(f"**Precio:** S/. {p['precio_venta']:.2f} | **Cat:** {p['categoria']}")
                    st.caption(p['descripcion'])
                
                # Botones de Acción
                with col_btns:
                    # MODAL DE EDICIÓN
                    if st.button("📝 Editar", key=f"edit_{p['id']}"):
                        st.session_state[f"editando_{p['id']}"] = True
                    
                    # BOTÓN DE ELIMINACIÓN
                    if st.button("🗑️ Eliminar", key=f"del_{p['id']}", type="secondary"):
                        db.table("productos").delete().eq("id", p['id']).execute()
                        st.warning(f"Producto {p['nombre']} eliminado.")
                        st.cache_data.clear()
                        st.rerun()

                # Formulario de Edición (se activa al presionar Editar)
                if st.session_state.get(f"editando_{p['id']}", False):
                    with st.form(f"form_edit_{p['id']}"):
                        st.write(f"--- Editando: {p['nombre']} ---")
                        nuevo_nom = st.text_input("Nombre", value=p['nombre'])
                        nueva_desc = st.text_area("Descripción", value=p['descripcion'])
                        nuevo_pre = st.number_input("Precio", value=float(p['precio_venta']))
                        nueva_cat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos"], index=0)
                        nueva_foto = st.file_uploader("Cambiar foto (opcional)", type=["jpg", "png"])
                        
                        col_save, col_cancel = st.columns(2)
                        if col_save.form_submit_button("Guardar Cambios"):
                            url_foto = p['imagen_url'] # Mantener la actual por defecto
                            if nueva_foto:
                                nombre_archivo = f"edit_{nuevo_nom.lower().replace(' ', '_')}"
                                url_foto = subir_imagen_producto(nueva_foto, nombre_archivo)
                            
                            db.table("productos").update({
                                "nombre": nuevo_nom, "descripcion": nueva_desc,
                                "precio_venta": nuevo_pre, "categoria": nueva_cat,
                                "imagen_url": url_foto
                            }).eq("id", p['id']).execute()
                            
                            st.session_state[f"editando_{p['id']}"] = False
                            st.cache_data.clear()
                            st.rerun()
                            
                        if col_cancel.form_submit_button("Cancelar"):
                            st.session_state[f"editando_{p['id']}"] = False
                            st.rerun()
    else:
        st.info("La carta está vacía.")
