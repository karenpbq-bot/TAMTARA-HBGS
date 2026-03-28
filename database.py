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
    """Sube una imagen al bucket 'fotos_productos' en Supabase."""
    db = conectar()
    try:
        img_bytes = archivo_imagen.getvalue()
        # Subir al Storage
        db.storage.from_("fotos_productos").upload(
            path=nombre_archivo,
            file=img_bytes,
            file_options={"content-type": archivo_imagen.type, "x-upsert": "true"}
        )
        # Retornar URL pública
        return db.storage.from_("fotos_productos").get_public_url(nombre_archivo)
    except Exception as e:
        st.error(f"Error en Storage: {e}")
        return None

@st.cache_data(ttl=300)
def obtener_productos():
    db = conectar()
    return db.table("productos").select("*").order("nombre").execute()
