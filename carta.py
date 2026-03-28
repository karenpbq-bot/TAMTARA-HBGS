import streamlit as st
from database import conectar, obtener_productos

def mostrar_modulo_carta():
    st.header("📋 Gestión de la Carta (Productos)")
    
    # 1. Formulario para crear el producto base
    with st.expander("➕ Registrar Nuevo Producto en la Carta"):
        with st.form("form_productos"):
            nombre = st.text_input("Nombre de la Hamburguesa / Producto")
            desc = st.text_area("Descripción (Ingredientes principales)")
            precio = st.number_input("Precio de Venta (S/.)", min_value=0.0, step=0.50)
            cat = st.selectbox("Categoría", ["Hamburguesas", "Bebidas", "Complementos", "Promos"])
            
            if st.form_submit_button("Guardar Producto"):
                if nombre and precio > 0:
                    db = conectar()
                    db.table("productos").insert({
                        "nombre": nombre,
                        "descripcion": desc,
                        "precio_venta": precio,
                        "categoria": cat
                    }).execute()
                    st.success(f"✅ {nombre} añadido a la carta.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("El nombre y el precio son obligatorios.")

    # 2. Ver productos actuales
    st.subheader("🖼️ Productos actuales")
    res = obtener_productos()
    if res.data:
        for p in res.data:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{p['nombre']}** - {p['categoria']}")
                col1.write(f"_{p['descripcion']}_")
                col2.subheader(f"S/. {p['precio_venta']:.2f}")
    else:
        st.info("La carta está vacía.")
