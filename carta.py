import streamlit as st
import pandas as pd
from database import conectar, obtener_productos, subir_imagen_producto
from PIL import Image, ImageOps
import io

def procesar_y_comprimir_imagen(archivo_subido, calidad=75):
    try:
        img = Image.open(archivo_subido)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer_final = io.BytesIO()
        img.save(buffer_final, format="JPEG", quality=calidad, optimize=True)
        buffer_final.seek(0)
        return buffer_final
    except Exception as e:
        st.error(f"Error procesando imagen: {e}")
        return None

def mostrar_modulo_carta():
    st.header("📋 Gestión de la Carta")
    db = conectar()
    
    # --- 1. REGISTRO DE NUEVO PRODUCTO ---
    with st.expander("➕ Registrar Nuevo Producto", expanded=False):
        with st.form("form_nuevo", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            nombre = c1.text_input("Nombre")
            precio = c2.number_input("Precio (S/.)", min_value=0.0, step=0.5)
            desc = st.text_area("Descripción")
            cat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos"])
            foto = st.file_uploader("Foto (Cualquier formato)", type=None)
            
            if st.form_submit_button("Guardar Producto"):
                url_foto = None
                if foto:
                    buf = procesar_y_comprimir_imagen(foto)
                    if buf:
                        nom_arc = f"prod_{nombre.lower().replace(' ','_')}.jpg"
                        url_foto = subir_imagen_producto(buf, nom_arc)
                
                db.table("productos").insert({
                    "nombre": nombre, "descripcion": desc, "precio_venta": precio, 
                    "categoria": cat, "imagen_url": url_foto
                }).execute()
                st.cache_data.clear()
                st.rerun()

    # --- 2. LISTADO CON EDICIÓN Y BORRADO ---
    res = obtener_productos()
    if res.data:
        for p in res.data:
            with st.container(border=True):
                col_img, col_info, col_acc = st.columns([1, 2, 1])
                
                with col_img:
                    img_url = p['imagen_url'] if p['imagen_url'] else "https://via.placeholder.com/150"
                    st.image(img_url, use_container_width=True)
                
                with col_info:
                    st.subheader(p['nombre'])
                    st.write(f"**S/. {p['precio_venta']:.2f}** | {p['categoria']}")
                    st.caption(p['descripcion'])
                
                with col_acc:
                    # Botones de control de estado
                    if st.button("📝 Editar", key=f"btn_ed_{p['id']}"):
                        st.session_state[f"editando_{p['id']}"] = True
                    
                    if st.button("🗑️ Borrar", key=f"btn_del_{p['id']}", type="secondary"):
                        db.table("productos").delete().eq("id", p['id']).execute()
                        st.cache_data.clear()
                        st.rerun()

                # --- FORMULARIO DESPLEGABLE DE EDICIÓN ---
                if st.session_state.get(f"editando_{p['id']}", False):
                    with st.form(f"edit_form_{p['id']}"):
                        st.info(f"Editando: {p['nombre']}")
                        enom = st.text_input("Nombre", value=p['nombre'])
                        epre = st.number_input("Precio", value=float(p['precio_venta']))
                        edesc = st.text_area("Descripción", value=p['descripcion'])
                        ecat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos"], 
                                          index=["Hamburguesas", "Bebidas", "Complementos"].index(p['categoria']))
                        efoto = st.file_uploader("Cambiar foto", type=None)
                        
                        c_save, c_can = st.columns(2)
                        if c_save.form_submit_button("Actualizar"):
                            e_url = p['imagen_url']
                            if efoto:
                                buf = procesar_y_comprimir_imagen(efoto)
                                if buf:
                                    e_url = subir_imagen_producto(buf, f"edit_{p['id']}.jpg")
                            
                            db.table("productos").update({
                                "nombre": enom, "precio_venta": epre, "descripcion": edesc,
                                "categoria": ecat, "imagen_url": e_url
                            }).eq("id", p['id']).execute()
                            st.session_state[f"editando_{p['id']}"] = False
                            st.cache_data.clear()
                            st.rerun()
                            
                        if c_can.form_submit_button("Cancelar"):
                            st.session_state[f"editando_{p['id']}"] = False
                            st.rerun()
    else:
        st.info("No hay productos.")
