import streamlit as st
import pandas as pd
from database import conectar, obtener_productos, subir_imagen_producto
from PIL import Image, ImageOps # Usaremos Pillow para el pulido
import io

def procesar_y_comprimir_imagen(archivo_subido, calidad=75):
    """
    Toma un archivo subido, verifica formato, corrige orientación y comprime.
    Retorna un objeto 'io.BytesIO' listo para subir.
    """
    try:
        # Abrir la imagen con Pillow
        img = Image.open(archivo_subido)
        
        # 1. Corregir orientación EXIF (para que no salga de costado)
        # Esto soluciona muchos problemas de fotos de celulares.
        img = ImageOps.exif_transpose(img)
        
        # 2. Convertir a RGB (necesario si es PNG con transparencia o formato HEIC)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # 3. Comprimir y guardar en un buffer de memoria
        buffer_final = io.BytesIO()
        
        # Guardar como JPEG comprimido para máxima velocidad de carga
        img.save(buffer_final, format="JPEG", quality=calidad, optimize=True)
        buffer_final.seek(0) # Resetear puntero para lectura
        
        return buffer_final
        
    except Exception as e:
        st.error(f"Error procesando la imagen: {e}. Intenta con otro formato.")
        return None

def mostrar_modulo_carta():
    st.header("📋 Gestión de la Carta (Productos)")
    db = conectar()
    
    # --- 1. FORMULARIO DE CREACIÓN CON PULIDO AUTOMÁTICO ---
    with st.expander("➕ Registrar Nuevo Producto", expanded=False):
        with st.form("form_nuevo_producto", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                nombre = st.text_input("Nombre del Producto")
                desc = st.text_area("Descripción")
            with col2:
                precio = st.number_input("Precio Venta (S/.)", min_value=0.0, step=0.50)
                cat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos"])
            
            # Subida sin restricciones de tipo, Pillow se encarga
            foto = st.file_uploader("Foto del producto (Pulido automático)", type=None, key="nueva_foto")
            
            if st.form_submit_button("Guardar Producto Completo"):
                if nombre and precio > 0:
                    url_foto = None
                    if foto:
                        with st.spinner("🔄 Puliendo y subiendo imagen..."):
                            # PROCESO DE PULIDO AUTOMÁTICO
                            buffer_pulido = procesar_y_comprimir_imagen(foto)
                            
                            if buffer_pulido:
                                # Usar el buffer pulido para subir
                                nombre_archivo = f"prod_{nombre.lower().replace(' ', '_')}.jpeg" # Forzamos extensión .jpeg
                                url_foto = subir_imagen_producto(buffer_pulido, nombre_archivo)
                    
                    db.table("productos").insert({
                        "nombre": nombre, "descripcion": desc, "precio_venta": precio, 
                        "categoria": cat, "imagen_url": url_foto
                    }).execute()
                    st.success("✅ Producto creado")
                    st.cache_data.clear()
                    st.rerun()

    # --- 2. GALERÍA DE PRODUCTOS ---
    st.subheader("🖼️ Productos en la Carta")
    res = obtener_productos()
    
    if res.data:
        # Usamos un sistema de cuadrícula (grilla)
        cols = st.columns(3)
        for idx, p in enumerate(res.data):
            # i % 3 nos da 0, 1 o 2 para asignar a las columnas
            with cols[idx % 3]:
                with st.container(border=True):
                    if p['imagen_url']:
                        st.image(p['imagen_url'], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                    
                    st.write(f"### {p['nombre']}")
                    st.write(f"**S/. {p['precio_venta']:.2f}** | *{p['categoria']}*")
                    st.caption(p['descripcion'])
                    
                    # Botón de eliminar con confirmación
                    if st.button("🗑️ Eliminar", key=f"del_{p['id']}", type="secondary"):
                        db.table("productos").delete().eq("id", p['id']).execute()
                        st.cache_data.clear()
                        st.rerun()
    else:
        st.info("La carta está vacía.")
