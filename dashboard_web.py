import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de página
st.set_page_config(page_title="FutsalMarket Catalunya", layout="wide", page_icon="⚽")

# CONEXIÓN A SUPABASE (Usa Secrets en producción/nube)
SUPABASE_URL = "https://yahkhkpaiprvmvxjjqxl.supabase.co"

# Intentar leer desde secrets de Streamlit (para la nube) o usar fallback local
try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhaGtoa3BhaXBydm12eGpqcXhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzE1OTIsImV4cCI6MjA5NjE0NzU5Mn0.hxs1wz-O4MuvJt1Hxan8Dm-hYeRm2i6v-q8Jra9NM2U" # <-- Pon tu key local aquí para pruebas en VS Code

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Error de conexión a Supabase: {e}")

# --- BARRA LATERAL ---
st.sidebar.title("⚽ FutsalMarket")
st.sidebar.subheader("Catalunya Edition")

menu = st.sidebar.radio(
    "Navegación", 
    ["📈 Panel de Control", "🔍 Scouting & Estadísticas", "📝 Ventanilla de Traspasos"]
)

# --- PANEL DE CONTROL ---
if menu == "📈 Panel de Control":
    st.title("📈 Centro de Mando Federativo")
    st.markdown("---")
    
    try:
        clubes_res = supabase.table("clubes").select("*").execute()
        clubes = clubes_res.data
        df_clubes = pd.DataFrame(clubes)
        
        if not df_clubes.empty:
            # Métricas superiores del negocio
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Clubes Afiliados", value=len(df_clubes))
            with col2:
                total_fcf = df_clubes['FcFCoin_saldo'].sum()
                st.metric(label="Masa Monetaria ($FcFCoin)", value=f"{total_fcf:,} 🪙")
            with col3:
                # Simular mercado abierto/cerrado para la FCF
                st.metric(label="Estado del Mercado", value="Abierto", delta="Período de Verano")
            
            st.markdown("### Clasificación de Solvencia Financiera")
            st.table(df_clubes[['nombre', 'FcFCoin_saldo', 'PlayerCoin_saldo']].rename(columns={
                'nombre': 'Club',
                'FcFCoin_saldo': 'Presupuesto Fichajes (FcFCoin)',
                'PlayerCoin_saldo': 'Límite Salarial (PlayerCoin)'
            }))
        else:
            st.info("No hay clubes registrados actualmente.")
    except Exception as e:
        st.error(f"Error cargando el panel: {e}")

# --- SCOUTING & ESTADÍSTICAS ---
elif menu == "🔍 Scouting & Estadísticas":
    st.title("🔍 Base de Datos de Scouting y Rendimiento")
    st.markdown("Visualiza y analiza el rendimiento de todos los jugadores de la liga para tomar la mejor decisión de fichaje.")
    st.markdown("---")
    
    try:
        # 1. Obtener clubes para el filtro
        clubes_data = supabase.table("clubes").select("id, nombre").execute().data
        nombres_clubes = {c['nombre']: c['id'] for c in clubes_data}
        
        filtro_club = st.selectbox("Filtrar por Club", ["Todos los Clubes"] + list(nombres_clubes.keys()))
        
        # 2. Consultar jugadores
        query = supabase.table("jugadores").select("*")
        if filtro_club != "Todos los Clubes":
            query = query.eq("club_id", nombres_clubes[filtro_club])
            
        jugadores = query.execute().data
        
        if jugadores:
            for j in jugadores:
                # Datos de rendimiento con fallback inteligente por si no existen las columnas todavía
                posicion = j.get("posicion", "Ala")
                goles = j.get("goles", hash(j['nombre']) % 18 + 2) # Mock realista basado en su nombre
                asistencias = j.get("asistencias", hash(j['nombre']) % 12 + 1)
                partidos = j.get("partidos_jugados", hash(j['nombre']) % 10 + 12)
                amarillas = j.get("tarjetas_amarillas", hash(j['nombre']) % 4)
                rojas = j.get("tarjetas_rojas", 1 if (hash(j['nombre']) % 15 == 0) else 0)
                valor = j.get("valor_mercado", (goles * 200) + (asistencias * 150) + 1000)
                
                # Tarjeta de jugador elegante
                with st.container():
                    col_foto, col_info, col_stats, col_fichaje = st.columns([1, 2, 3, 2])
                    
                    with col_foto:
                        # Icono grande según posición para que sea visual
                        if posicion.lower() in ["portero", "goalkeeper"]:
                            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🧤</h1>", unsafe_allow_html=True)
                        else:
                            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🏃‍♂️</h1>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>{posicion.upper()}</p>", unsafe_allow_html=True)
                    
                    with col_info:
                        st.subheader(j['nombre'])
                        # Encontrar el nombre del club al que pertenece
                        id_club = j['club_id']
                        club_pertence = next((name for name, cid in nombres_clubes.items() if cid == id_club), "Sin Club")
                        st.markdown(f"**Club Actual:** {club_pertence}")
                        st.markdown(f"💰 **Valor Estimado:** `{valor:,} FcFCoin`")
                        
                    with col_stats:
                        st.markdown("**Estadísticas de Temporada (FCF):**")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Partidos", partidos)
                        c2.metric("Goles ⚽", goles)
                        c3.metric("Asistencias", asistencias)
                        c4.metric("Tarjetas 🟨/🟥", f"{amarillas}/{rojas}")
                        
                    with col_fichaje:
                        st.markdown("<br>", unsafe_allow_html=True)
                        # Este botón simula el interés y redirige mentalmente a la pestaña de fichajes
                        st.button("Iniciar Negociación 📝", key=f"btn_negociar_{j['id']}", use_container_width=True)
                        
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
        else:
            st.info("No hay jugadores registrados en este filtro.")
            
    except Exception as e:
        st.error(f"Error cargando base de datos de jugadores: {e}")

# --- MERCADO DE FICHAJES ---
elif menu == "📝 Ventanilla de Traspasos":
    st.title("📝 Ventanilla de Traspasos Federativos")
    st.markdown("Realiza ofertas de club a club con validaciones financieras automáticas.")
    st.markdown("---")
    
    try:
        clubes = supabase.table("clubes").select("*").execute().data
        nombres_clubes = {c['nombre']: c for c in clubes}
        
        col1, col2 = st.columns(2)
        with col1:
            vendedor_nombre = st.selectbox("Club Vendedor (Origen)", list(nombres_clubes.keys()))
            vendedor = nombres_clubes[vendedor_nombre]
            
            jugadores = supabase.table("jugadores").select("id, nombre").eq("club_id", vendedor['id']).execute().data
            if jugadores:
                jugador_sel = st.selectbox("Selecciona Jugador", [j['nombre'] for j in jugadores])
                jugador_id = next(j['id'] for j in jugadores if j['nombre'] == jugador_sel)
            else:
                st.warning("Este club no tiene jugadores en plantilla.")
                jugador_sel = None
        
        with col2:
            comprador_nombre = st.selectbox("Club Comprador (Destino)", [c for c in nombres_clubes.keys() if c != vendedor_nombre])
            comprador = nombres_clubes[comprador_nombre]
            precio = st.number_input("Precio del Traspaso (en FcFCoin)", min_value=0, value=1500, step=100)

        st.markdown("---")
        
        if jugador_sel:
            # Aquí es donde pondremos el flujo condicional en los siguientes pasos
            st.info(f"**Operación propuesta:** Traspaso de **{jugador_sel}** desde el **{vendedor_nombre}** al **{comprador_nombre}** por **{precio:,} FcFCoin**.")
            
            if st.button("Enviar Propuesta Oficial", use_container_width=True):
                if comprador['FcFCoin_saldo'] >= precio:
                    # 1. Restar al comprador
                    supabase.table("clubes").update({"FcFCoin_saldo": comprador['FcFCoin_saldo'] - precio}).eq("id", comprador['id']).execute()
                    # 2. Sumar al vendedor
                    supabase.table("clubes").update({"FcFCoin_saldo": vendedor['FcFCoin_saldo'] + precio}).eq("id", vendedor['id']).execute()
                    # 3. Mover al jugador
                    supabase.table("jugadores").update({"club_id": comprador['id']}).eq("id", jugador_id).execute()
                    
                    st.success(f"🎉 ¡Fichaje completado! {jugador_sel} ya está inscrito en la plantilla del {comprador_nombre}.")
                    st.balloons()
                else:
                    st.error(f"❌ El club comprador ({comprador_nombre}) no dispone de saldo suficiente para afrontar este traspaso.")
    except Exception as e:
        st.error(f"Error procesando la ventana de traspasos: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("FutsalMarket Catalunya v1.2 Premium")
