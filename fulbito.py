import streamlit as st
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Vacaciones 2027", page_icon="✈️")

TOTAL_REQUERIDO = 11

st.title("✈️ Organizador de Vacaciones")
st.write(f"Ingresá tus fechas disponibles. Cuando respondan las **{TOTAL_REQUERIDO} personas**, la app mostrará las coincidencias.")

# --- ESTADO GLOBAL (Persistente entre usuarios) ---
if "respuestas" not in st.session_state:
    st.session_state.respuestas = {}  # { "Nombre": set(dias) }

# --- ESTADO TEMPORAL DE SESIÓN (Para la persona actual) ---
if "mis_rangos" not in st.session_state:
    st.session_state.mis_rangos = []  # Lista de rangos cargados antes de guardar

nombre = st.text_input("Tu nombre:").strip()

st.markdown("---")
st.subheader("📅 Carga tus rangos de disponibilidad")

# Selector de fechas individual
rango_actual = st.date_input(
    "Seleccioná un rango de fechas:",
    value=(date.today(), date.today() + timedelta(days=7)),
    format="DD/MM/YYYY",
    key="selector_fecha"
)

# Botón para ir sumando rangos
if st.button("➕ Agregar este rango a mi lista"):
    if len(rango_actual) == 2:
        st.session_state.mis_rangos.append(rango_actual)
        st.success(f"Rango agregado: {rango_actual[0].strftime('%d/%m')} al {rango_actual[1].strftime('%d/%m')}")
    else:
        st.error("Por favor seleccioná un rango completo (fecha de inicio y fin).")

# Muestra los rangos agregados hasta el momento
if st.session_state.mis_rangos:
    st.write("**Tus rangos cargados:**")
    for i, r in enumerate(st.session_state.mis_rangos, 1):
        st.info(f"Opción {i}: Del {r[0].strftime('%d/%m/%Y')} al {r[1].strftime('%d/%m/%Y')}")

# Botón final para confirmar y guardar en la base global
st.markdown("---")
if st.button("💾 Guardar TODAS mis fechas", type="primary"):
    if not nombre:
        st.error("Por favor ingresá tu nombre arriba de todo.")
    elif not st.session_state.mis_rangos:
        st.error("Tenés que agregar al menos un rango de fechas.")
    elif nombre in st.session_state.respuestas:
        st.warning(f"⚠️ {nombre}, ya habías guardado tus fechas.")
    else:
        # Generar el conjunto total de días combinando todos los rangos cargados
        dias_totales = set()
        for f_inicio, f_fin in st.session_state.mis_rangos:
            actual = f_inicio
            while actual <= f_fin:
                dias_totales.add(actual)
                actual += timedelta(days=1)

        # Guardar en la estructura principal
        st.session_state.respuestas[nombre] = dias_totales
        
        # Limpiar la memoria temporal de rangos para el siguiente usuario
        st.session_state.mis_rangos = []
        st.success(f"¡Excelente {nombre}! Todos tus rangos fueron registrados.")

# --- ESTADO DE LA VOTACIÓN ---
st.divider()
cant_respuestas = len(st.session_state.respuestas)
st.metric(label="Personas que ya cargaron", value=f"{cant_respuestas} / {TOTAL_REQUERIDO}")

if cant_respuestas > 0:
    st.write("**Ya respondieron:**", ", ".join(st.session_state.respuestas.keys()))

# --- RESULTADO FINAL (Cuando responden las 10) ---
if cant_respuestas >= TOTAL_REQUERIDO:
    st.subheader("🎉 ¡Todas respondieron! Buscando coincidencias...")
    
    # Intersección de todos los conjuntos de fechas
    coincidencias = set.intersection(*st.session_state.respuestas.values())
    
    if coincidencias:
        dias_ordenados = sorted(list(coincidencias))
        inicio_str = dias_ordenados[0].strftime("%d/%m/%Y")
        fin_str = dias_ordenados[-1].strftime("%d/%m/%Y")
        
        st.balloons()
        st.success(f"### 📅 Coincidencia encontrada:\nDel **{inicio_str}** al **{fin_str}** ({len(dias_ordenados)} días en total).")
    else:
        st.error("❌ No hay ninguna fecha en la que coincidan las 10 personas al mismo tiempo.")

# Reiniciar por si quieren volver a empezar
if st.button("Reiniciar votación general"):
    st.session_state.respuestas = {}
    st.session_state.mis_rangos = []
    st.rerun()
