import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración
st.set_page_config(page_title="FutsalMarket Pro", layout="wide", page_icon="⚽")

# CONEXIÓN
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- SIDEBAR PROFESIONAL ---
st.sidebar.image("https://img.icons8.com/color/96/000000/soccer-ball.png", width=60)
st.sidebar.title("FutsalMarket Pro")
menu = st.sidebar.radio("Navegación", ["Panel de Control", "Auditoría de Clubes", "Mercado de Fichajes"])

# --- PANEL DE CONTROL ---
if menu == "Panel de Control":
    st.title("📊 Panel de Control Ejecutivo")
    clubes = supabase.table("clubes").select("*").execute().data
    df = pd.DataFrame(clubes)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Clubes Activos", len(df))
    col2.metric("Liquidez Total CIF", f"{df['FcFCoin_saldo'].sum():,}")
    col3.metric("Avales FGS", f"{df['PlayerCoin_saldo'].sum():,}")
    
    st.subheader("Clasificación Financiera")
    st.dataframe(df[['nombre', 'FcFCoin_saldo', 'PlayerCoin_saldo']].sort_values(by='FcFCoin_saldo', ascending=False), use_container_width=True)

# --- AUDITORÍA ---
elif menu == "Auditoría de Clubes":
    st.title("🔍 Auditoría Federativa")
    clubes_data = supabase.table("clubes").select("id, nombre").execute().data
    nombres_clubes = {c['nombre']: c['id'] for c in clubes_data}
    seleccion = st.selectbox("Selecciona club a auditar:", list(nombres_clubes.keys()))
    
    jugadores = supabase.table("jugadores").select("nombre, posicion").eq("club_id", nombres_clubes[seleccion]).execute().data
    st.subheader(f"Plantilla: {seleccion}")
    st.table(pd.DataFrame(jugadores))

# --- MERCADO DE FICHAJES ---
elif menu == "Mercado de Fichajes":
    st.title("📝 Ventanilla de Traspasos Pro")
    clubes = supabase.table("clubes").select("*").execute().data
    nombres_clubes = {c['nombre']: c for c in clubes}
    
    c1, c2 = st.columns(2)
    with c1:
        vendedor_nombre = st.selectbox("Club Vendedor", list(nombres_clubes.keys()))
        vendedor = next(c for c in clubes if c['nombre'] == vendedor_nombre)
        jugadores = supabase.table("jugadores").select("id, nombre").eq("club_id", vendedor['id']).execute().data
        jugador_sel = st.selectbox("Jugador", [j['nombre'] for j in jugadores])
        jugador_id = next(j['id'] for j in jugadores if j['nombre'] == jugador_sel)
    
    with c2:
        comprador_nombre = st.selectbox("Club Comprador", [c for c in nombres_clubes.keys() if c != vendedor_nombre])
        comprador = next(c for c in clubes if c['nombre'] == comprador_nombre)
        precio = st.number_input("Precio del traspaso (CIF)", min_value=0, value=1000)

    if st.button("Ejecutar Traspaso", type="primary"):
        if comprador['FcFCoin_saldo'] >= precio:
            supabase.table("clubes").update({"FcFCoin_saldo": comprador['FcFCoin_saldo'] - precio}).eq("id", comprador['id']).execute()
            supabase.table("clubes").update({"FcFCoin_saldo": vendedor['FcFCoin_saldo'] + precio}).eq("id", vendedor['id']).execute()
            supabase.table("jugadores").update({"club_id": comprador['id']}).eq("id", jugador_id).execute()
            st.success(f"¡Traspaso oficializado! {jugador_sel} es nuevo jugador del {comprador_nombre}.")
        else:
            st.error("❌ Fondos insuficientes.")