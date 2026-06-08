import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de página
st.set_page_config(page_title="FutsalMarket Catalunya", layout="wide", page_icon="⚽")

# CONEXIÓN A SUPABASE
SUPABASE_URL = "https://yahkhkpaiprvmvxjjqxl.supabase.co"

try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_KEY = "TU_KEY_LARGA_AQUÍ" # <-- Pon tu key local para pruebas en VS Code

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

# Cargar clubes para simular sesión
try:
    clubes_lista = supabase.table("clubes").select("id, nombre").execute().data
    nombres_clubes = {c['nombre']: c for c in clubes_lista}
except Exception:
    nombres_clubes = {}

st.sidebar.markdown("---")
# SIMULACIÓN DE SESIÓN (Workspace)
st.sidebar.markdown("### 🏢 Tu Espacio de Trabajo")
club_activo_nombre = st.sidebar.selectbox("Gestionar como Club:", list(nombres_clubes.keys()))
club_activo = nombres_clubes.get(club_activo_nombre)

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menú de Operaciones", 
    ["📈 Panel de Control", "🔍 Scouting & Estadísticas", "📝 Ventanilla de Traspasos", "📥 Buzón de Ofertas"]
)

# --- PANEL DE CONTROL ---
if menu == "📈 Panel de Control":
    st.title("📈 Centro de Mando Federativo")
    st.markdown(f"Sesión activa: **{club_activo_nombre}**")
    st.markdown("---")
    
    try:
        clubes_res = supabase.table("clubes").select("*").execute()
        df_clubes = pd.DataFrame(clubes_res.data)
        
        if not df_clubes.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Clubes Afiliados", value=len(df_clubes))
            with col2:
                total_fcf = df_clubes['FcFCoin_saldo'].sum()
                st.metric(label="Masa Monetaria ($FcFCoin)", value=f"{total_fcf:,} 🪙")
            with col3:
                st.metric(label="Estado del Mercado", value="Abierto", delta="Período de Verano")
            
            st.markdown("### Clasificación de Solvencia Financiera (Tercera Nacional)")
            st.table(df_clubes[['nombre', 'FcFCoin_saldo', 'PlayerCoin_saldo']].rename(columns={
                'nombre': 'Club',
                'FcFCoin_saldo': 'Créditos de Inscripción (CIF)',
                'PlayerCoin_saldo': 'Fondo de Garantía Salarial (FGS)'
            }))
        else:
            st.info("No hay clubes registrados.")
    except Exception as e:
        st.error(f"Error cargando el panel: {e}")

# --- SCOUTING & ESTADÍSTICAS ---
elif menu == "🔍 Scouting & Estadísticas":
    st.title("🔍 Base de Datos de Scouting y Rendimiento")
    st.markdown("---")
    
    try:
        filtro_club = st.selectbox("Filtrar por Club", ["Todos los Clubes"] + list(nombres_clubes.keys()))
        
        query = supabase.table("jugadores").select("*")
        if filtro_club != "Todos los Clubes":
            query = query.eq("club_id", nombres_clubes[filtro_club]['id'])
            
        jugadores = query.execute().data
        
        if jugadores:
            for j in jugadores:
                posicion = j.get("posicion", "Ala")
                goles = j.get("goles", hash(j['nombre']) % 18 + 2)
                asistencias = j.get("asistencias", hash(j['nombre']) % 12 + 1)
                partidos = j.get("partidos_jugados", hash(j['nombre']) % 10 + 12)
                amarillas = j.get("tarjetas_amarillas", hash(j['nombre']) % 4)
                rojas = j.get("tarjetas_rojas", 1 if (hash(j['nombre']) % 15 == 0) else 0)
                valor = j.get("valor_mercado", (goles * 200) + (asistencias * 150) + 1000)
                
                with st.container():
                    col_foto, col_info, col_stats = st.columns([1, 2, 4])
                    
                    with col_foto:
                        if posicion.lower() in ["portero", "goalkeeper"]:
                            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🧤</h1>", unsafe_allow_html=True)
                        else:
                            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🏃‍♂️</h1>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>{posicion.upper()}</p>", unsafe_allow_html=True)
                    
                    with col_info:
                        st.subheader(j['nombre'])
                        id_club = j['club_id']
                        club_pertence = next((name for name, c in nombres_clubes.items() if c['id'] == id_club), "Sin Club")
                        st.markdown(f"**Club Actual:** {club_pertence}")
                        st.markdown(f"💰 **Valor de Referencia:** `{valor:,} CIF`")
                        
                    with col_stats:
                        st.markdown("**Estadísticas de Temporada (FCF):**")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Partidos", partidos)
                        c2.metric("Goles ⚽", goles)
                        c3.metric("Asistencias", asistencias)
                        c4.metric("Tarjetas 🟨/🟥", f"{amarillas}/{rojas}")
                        
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
        else:
            st.info("No hay jugadores registrados.")
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")

# --- VENTANILLA DE TRASPASOS (SISTEMA DE OFERTAS) ---
elif menu == "📝 Ventanilla de Traspasos":
    st.title("📝 Ventanilla de Ofertas Oficiales")
    st.markdown(f"Club Comprador (Tú): **{club_activo_nombre}**")
    st.markdown("---")
    
    try:
        # 1. Seleccionar Club Vendedor
        club_vendedor_nombre = st.selectbox("Club Vendedor (Origen)", [c for c in nombres_clubes.keys() if c != club_activo_nombre])
        vendedor = nombres_clubes[club_vendedor_nombre]
        
        # 2. Seleccionar Jugador
        jugadores = supabase.table("jugadores").select("id, nombre").eq("club_id", vendedor['id']).execute().data
        
        if jugadores:
            jugador_sel = st.selectbox("Selecciona Jugador", [j['nombre'] for j in jugadores])
            jugador_id = next(j['id'] for j in jugadores if j['nombre'] == jugador_sel)
            
            # 3. Fijar las propuestas financieras
            col1, col2 = st.columns(2)
            with col1:
                precio_cif = st.number_input("Derechos de Transferencia para el Club (CIF 🪙)", min_value=0, value=2000, step=500)
            with col2:
                salario_fgs = st.number_input("Garantía Salarial para el Jugador (FGS 💎)", min_value=0, value=800, step=100)
                
            st.markdown("---")
            st.info(f"**Resumen del Trámite:** Se enviará una propuesta formal al **{club_vendedor_nombre}** por la cesión de derechos de **{jugador_sel}** por un importe de **{precio_cif:,} CIF** y un salario garantizado de **{salario_fgs:,} FGS**.")
            
            if st.button("Enviar Propuesta de Fichaje", use_container_width=True):
                # Verificar si el comprador tiene fondos antes de dejarle enviar la oferta
                club_comprador_full = supabase.table("clubes").select("*").eq("id", club_activo['id']).execute().data[0]
                
                if club_comprador_full['FcFCoin_saldo'] < precio_cif:
                    st.error("❌ Tu club no dispone de suficientes Créditos de Inscripción (CIF) para realizar esta oferta.")
                elif club_comprador_full['PlayerCoin_saldo'] < salario_fgs:
                    st.error("❌ Tu club no dispone de suficiente Fondo de Garantía Salarial (FGS) para avalar el sueldo del jugador.")
                else:
                    # Registramos la oferta en la base de datos en estado 'pendiente'
                    oferta_data = {
                        "jugador_id": jugador_id,
                        "vendedor_id": vendedor['id'],
                        "comprador_id": club_activo['id'],
                        "oferta_cif": precio_cif,
                        "oferta_fgs": salario_fgs,
                        "estado": "pendiente"
                    }
                    supabase.table("ofertas_fichaje").insert(oferta_data).execute()
                    st.success(f"📩 ¡Propuesta enviada con éxito! Queda a la espera de que la junta de {club_vendedor_nombre} acepte las condiciones en su buzón.")
        else:
            st.warning("Este club no tiene jugadores registrados en su plantilla actualmente.")
            
    except Exception as e:
        st.error(f"Error al tramitar la oferta: {e}")

# --- BUZÓN DE OFERTAS (EL DESPACHO) ---
elif menu == "📥 Buzón de Ofertas":
    st.title("📥 Buzón de Ofertas Oficiales")
    st.markdown(f"Club Actual: **{club_activo_nombre}**")
    st.markdown("---")
    
    try:
        # Cargar ofertas recibidas por nuestro club como vendedor
        ofertas = supabase.table("ofertas_fichaje").select(
            "id, jugador_id, jugadores(nombre), comprador_id, clubes(nombre), oferta_cif, oferta_fgs, estado"
        ).eq("vendedor_id", club_activo['id']).eq("estado", "pendiente").execute().data
        
        if not ofertas:
            st.info("No tienes propuestas de fichaje pendientes de resolución en este momento.")
        else:
            for o in ofertas:
                jugador_nombre = o['jugadores']['nombre']
                club_comprador = o['clubes']['nombre']
                cif_ofrecido = o['oferta_cif']
                fgs_ofrecido = o['oferta_fgs']
                
                with st.container():
                    col_detalles, col_acciones = st.columns([3, 1])
                    with col_detalles:
                        st.subheader(f"Oferta por {jugador_nombre}")
                        st.markdown(f"🏢 **Club Interesado:** {club_comprador}")
                        st.markdown(f"💰 **Derechos propuestos:** `{cif_ofrecido:,} CIF` | 💎 **Sueldo Jugador:** `{fgs_ofrecido:,} FGS`")
                    
                    with col_acciones:
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_si, col_no = st.columns(2)
                        
                        # BOTÓN ACEPTAR
                        if col_si.button("✅", key=f"acp_{o['id']}", use_container_width=True):
                            # Realizamos la transacción real en la base de datos
                            # 1. Obtener saldos actualizados del comprador y vendedor
                            vendedor_full = supabase.table("clubes").select("*").eq("id", club_activo['id']).execute().data[0]
                            comprador_full = supabase.table("clubes").select("*").eq("id", o['comprador_id']).execute().data[0]
                            
                            # Validar que el comprador sigue teniendo los fondos
                            if comprador_full['FcFCoin_saldo'] >= cif_ofrecido and comprador_full['PlayerCoin_saldo'] >= fgs_ofrecido:
                                # A) Restar al comprador
                                supabase.table("clubes").update({
                                    "FcFCoin_saldo": comprador_full['FcFCoin_saldo'] - cif_ofrecido,
                                    "PlayerCoin_saldo": comprador_full['PlayerCoin_saldo'] - fgs_ofrecido
                                }).eq("id", comprador_full['id']).execute()
                                
                                # B) Sumar al vendedor (recibe los CIF)
                                supabase.table("clubes").update({
                                    "FcFCoin_saldo": vendedor_full['FcFCoin_saldo'] + cif_ofrecido
                                }).eq("id", vendedor_full['id']).execute()
                                
                                # C) Cambiar el club del jugador
                                supabase.table("jugadores").update({"club_id": comprador_full['id']}).eq("id", o['jugador_id']).execute()
                                
                                # D) Actualizar estado de la oferta
                                supabase.table("ofertas_fichaje").update({"estado": "completada"}).eq("id", o['id']).execute()
                                
                                st.success(f"🎉 ¡Fichaje completado! {jugador_nombre} se incorpora al {club_comprador}.")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ La operación ha fallado: El club comprador ya no dispone de los fondos suficientes.")
                        
                        # BOTÓN RECHAZAR
                        if col_no.button("❌", key=f"rch_{o['id']}", use_container_width=True):
                            supabase.table("ofertas_fichaje").update({"estado": "rechazada"}).eq("id", o['id']).execute()
                            st.warning("Propuesta de transferencia declinada.")
                            st.rerun()
                            
                st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Error al cargar el buzón: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("FutsalMarket Catalunya v1.5 Premium")
