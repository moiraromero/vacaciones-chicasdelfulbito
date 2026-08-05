import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Vacaciones 2027", page_icon="✈️")

TOTAL_REQUERIDO = 11

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
    "Seleccioná un rango de fechas:",
    value=(date.today(), date.today() + timedelta(days=7)),
    format="DD/MM/YYYY"
)

if st.button("💾 Guardar mis fechas", type="primary"):
    if not nombre:
        st.error("Por favor ingresá tu nombre.")
    elif len(rango_actual) != 2:
        st.error("Seleccioná un rango completo.")
    elif nombre in personas_votaron:
        st.warning(f"⚠️ {nombre}, ya habías cargado tus fechas.")
    else:
        sheet = obtener_sheet()
        f_inicio = rango_actual[0].strftime("%Y-%m-%d")
        f_fin = rango_actual[1].strftime("%Y-%m-%d")
        
        # Guardar la nueva fila directamente en la planilla
        sheet.append_row([nombre, f_inicio, f_fin])
        
        st.success(f"¡Listo {nombre}! Fechas registradas.")
        st.rerun()

# --- ESTADO DE LA VOTACIÓN ---
st.divider()
st.metric(label="Personas que ya cargaron", value=f"{cant_respuestas} / {TOTAL_REQUERIDO}")

if cant_respuestas > 0:
    st.write("**Ya respondieron:**", ", ".join(personas_votaron))

# --- CÁLCULO FINAL (Cuando llegan a 11) ---
if cant_respuestas >= TOTAL_REQUERIDO:
    st.subheader("🎉 ¡Todas respondieron! Analizando coincidencias...")
    
    dicc_dias = {}
    for _, row in df_respuestas.iterrows():
        n = str(row["Nombre"])
        f_i = datetime.strptime(str(row["Fecha_Inicio"]), "%Y-%m-%d").date()
        f_f = datetime.strptime(str(row["Fecha_Fin"]), "%Y-%m-%d").date()
        
        dias = {f_i + timedelta(days=i) for i in range((f_f - f_i).days + 1)}
        
        if n in dicc_dias:
            dicc_dias[n].update(dias)
        else:
            dicc_dias[n] = dias
            
    coincidencias = set.intersection(*dicc_dias.values())
    
    if coincidencias:
        dias_ord = sorted(list(coincidencias))
        st.balloons()
        st.success(f"### 📅 Coincidencia encontrada:\nDel **{dias_ord[0].strftime('%d/%m/%Y')}** al **{dias_ord[-1].strftime('%d/%m/%Y')}**.")
    else:
        st.error("❌ No hay ninguna fecha en la que coincidan las 11 personas al mismo tiempo.")
