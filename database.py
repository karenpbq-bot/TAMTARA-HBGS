import streamlit as st
from supabase import create_client

# Usamos cache_resource para que la conexión no se abra y cierre mil veces
@st.cache_resource
def conectar():
    # Estas llaves las configuraremos luego en los Secrets de Streamlit
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Función para traer insumos (lista de materiales) con caché de 5 minutos
@st.cache_data(ttl=300)
def obtener_insumos():
    db = conectar()
    return db.table("insumos").select("*").order("nombre").execute()

# Agregar esta función al final de database.py
@st.cache_data(ttl=300)
def obtener_productos():
    db = conectar()
    return db.table("productos").select("*").order("nombre").execute()
    
# --- AGREGAR ESTO AL FINAL DE database.py ---

def subir_imagen_producto(archivo_imagen, nombre_archivo):
    """Sube una imagen al bucket público de forma forzada."""
    db = conectar()
    try:
        # 1. Preparar los datos
        img_bytes = archivo_imagen.getvalue()
        
        # 2. Subir con parámetros de limpieza (upsert=true para sobreescribir)
        # Forzamos el content-type para que Supabase lo reconozca como imagen
        db.storage.from_("fotos_productos").upload(
            path=nombre_archivo,
            file=img_bytes,
            file_options={
                "content-type": "image/jpeg", 
                "x-upsert": "true"
            }
        )
        
        # 3. Obtener la URL limpia
        url = db.storage.from_("fotos_productos").get_public_url(nombre_archivo)
        
        # Limpieza de parámetros de cache (?t=...)
        if "?" in url:
            url = url.split("?")[0]
            
        return url
        
    except Exception as e:
        # Si el error es que ya existe, intentamos solo obtener la URL
        if "already exists" in str(e):
            return db.storage.from_("fotos_productos").get_public_url(nombre_archivo).split("?")[0]
        
        st.error(f"Error técnico de Storage: {e}")
        return None
