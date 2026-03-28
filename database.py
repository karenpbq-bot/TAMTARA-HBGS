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
