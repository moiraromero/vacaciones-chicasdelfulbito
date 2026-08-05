import streamlit as st
from datetime import datetime, date, timedelta
from collections import Counter
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Vacaciones 2027", page_icon="✈️")

TOTAL_REQUERIDO = 4

st.title("✈️ Organizador de Vacaciones")

# --- CONEXIÓN A GOOGLE SHEETS VIA GSPREAD ---
@st.cache_resource
def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client

def obtener_sheet():
    client = get_gsheet_client()
    url = st.secrets["sheets"]["spreadsheet_url"]
    return client.open_by_url(url).sheet1

def cargar_respuestas():
    try:
        sheet = obtener_sheet()
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame(columns=["Nombre", "Fecha_Inicio", "Fecha_Fin"])

df_respuestas = cargar_respuestas()

# --- CÁLCULO DE QUIÉNES YA VOTARON ---
personas_votaron = df_respuestas["Nombre"].unique().tolist() if not df_respuestas.empty else []
cant_respuestas = len(personas_votaron)

# --- FORMULARIO ---
nombre = st.text_input("Tu nombre:").strip()

rango_actual = st.date_input(
    "Seleccioná un rango de fechas disponible:",
    value=(date.today(), date.today() + timedelta(days=7)),
    format="DD/MM/YYYY"
)

if st.button("💾 Guardar rango de fechas", type="primary"):
    if not nombre:
        st.error("Por favor ingresá tu nombre.")
    elif len(rango_actual) != 2:
        st.error("Seleccioná un rango completo (fecha inicial y final).")
    else:
        sheet = obtener_sheet()
        f_inicio = rango_actual[0].strftime("%Y-%m-%d")
        f_fin = rango_actual[1].strftime("%Y-%m-%d")
        
        sheet.append_row([nombre, f_inicio, f_fin])
        
        st.success(f"¡Listo {nombre}! Rango guardado correctamente.")
        st.rerun()

# --- ESTADO DE LA VOTACIÓN ---
st.divider()
st.metric(label="Personas que ya cargaron sus fechas", value=f"{cant_respuestas} / {TOTAL_REQUERIDO}")

if cant_respuestas > 0:
    st.write("**Ya cargaron disponibilidad:**", ", ".join(personas_votaron))

# --- CÁLCULO FINAL DE COINCIDENCIAS ---
if cant_respuestas > 0:
    st.subheader("📊 Análisis de coincidencias de fechas")
    
    # Unificar los días disponibles de cada persona (evitando duplicados por usuario)
    dicc_dias = {}
    for _, row in df_respuestas.iterrows():
        n = str(row["Nombre"]).strip()
        f_i = datetime.strptime(str(row["Fecha_Inicio"]), "%Y-%m-%d").date()
        f_f = datetime.strptime(str(row["Fecha_Fin"]), "%Y-%m-%d").date()
        
        dias = {f_i + timedelta(days=i) for i in range((f_f - f_i).days + 1)}
        
        if n in dicc_dias:
            dicc_dias[n].update(dias)
        else:
            dicc_dias[n] = dias
            
    # Contar cuántas personas coinciden en cada fecha individual
    conteo_dias = Counter()
    for n, dias in dicc_dias.items():
        for d in dias:
            conteo_dias[d] += 1
            
    if conteo_dias:
        max_personas = max(conteo_dias.values())
        dias_maximos = sorted([d for d, cant in conteo_dias.items() if cant == max_personas])
        
        if max_personas == TOTAL_REQUERIDO:
            st.balloons()
            st.success(f"🎉 **¡Coincidencia perfecta de los {TOTAL_REQUERIDO}!**")
        else:
            st.warning(f"⚠️ Máxima coincidencia alcanzada: **{max_personas} de {cant_respuestas} personas** coinciden en los mismos días.")
            
        # Agrupar fechas consecutivas para mostrar rangos claros
        rangos = []
        if dias_maximos:
            inicio = dias_maximos[0]
            fin = dias_maximos[0]
            
            for d in dias_maximos[1:]:
                if d == fin + timedelta(days=1):
                    fin = d
                else:
                    rangos.append((inicio, fin))
                    inicio = d
                    fin = d
            rangos.append((inicio, fin))
            
        st.write(f"**Mejores fechas encontradas ({max_personas} personas):**")
        for r_inicio, r_fin in rangos:
            dias_totales = (r_fin - r_inicio).days + 1
            if r_inicio == r_fin:
                st.write(f"• **{r_inicio.strftime('%d/%m/%Y')}** (1 día)")
            else:
                st.write(f"• Del **{r_inicio.strftime('%d/%m/%Y')}** al **{r_fin.strftime('%d/%m/%Y')}** ({dias_totales} días)")
                
# --- SECCIÓN DE RESETEO EN LA BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Opciones de administración")
    if st.button("🗑️ Resetear votación / Borrar datos"):
        sheet = obtener_sheet()
        sheet.resize(rows=1)
        st.success("¡Se borraron todas las respuestas!")
        st.rerun()
