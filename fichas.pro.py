import streamlit as st
from fpdf import FPDF
import datetime
import urllib.parse
import os

# --- 1. SEGURIDAD Y LLAVE MAESTRA ---
CLAVES_PRO = st.secrets["claves_autorizadas"]

if "usos" not in st.session_state:
    st.session_state["usos"] = 0
if "es_pro" not in st.session_state:
    st.session_state["es_pro"] = False

# --- 2. DISEÑO CORPORATIVO ---
st.set_page_config(page_title="Gestión Estética Profesional", layout="wide")

def apply_custom_design():
    st.markdown("""
        <style>
        .stApp { background-color: #fdfaf8; }
        [data-testid="stSidebar"] { background-color: #f8f1ed; }
        .stButton>button { border-radius: 20px; background-color: #d4a373; color: white; width: 100%; border: none; }
        .stDownloadButton>button { border-radius: 20px; background-color: #606c38; color: white; width: 100%; border: none; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { 
            background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 10px 10px 0 0; padding: 10px 20px; 
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# --- 3. BASE DE DATOS DE SERVICIOS ---
SERVICIOS = {
    "Extensiones de Pestañas": {
        "desc": "Acepto que extensiones de pestañas sean aplicadas y / o eliminadas de mis pestañas. Antes de que mi técnico calificado en pestañas profesionales pueda realizar este procedimiento, entiendo que debo completar este acuerdo y dar mi consentimiento.",
        "riesgos": "Irritación ocular, dolor ocular, comezón en los ojos, malestar, y en casos excepcionales infección ocular.",
        "clausulas": [
            "Entiendo que hay riesgos asociados con la aplicación y/o eliminación de pestañas artificiales.",
            "Las extensiones se aplicarán según determine el técnico para no crear un peso excesivo preservando la salud natural.",
            "Si experimento problemas, me pondré en contacto con mi técnico para el retiro y consultaré a un médico por mi cuenta.",
            "Los materiales adhesivos pueden alojarse durante o después del procedimiento e irritar mis ojos.",
            "El incumplimiento de las instrucciones de cuidado posterior puede hacer que las extensiones se caigan."
        ],
        "cuidados_wa": "\n✅ No mojarlas las primeras 24-48 horas.\n✅ Cepillarlas diariamente con el cepillo limpio.\n✅ Usar solo productos de limpieza base agua (sin aceites).\n✅ Dormir boca arriba para evitar fricción.\n🚫 No frotar los ojos ni arrancar las extensiones."
    },
    "Limpieza Facial Profunda": {
        "desc": "Tratamiento que a través de agua y puntas de diamante realiza una limpieza profunda, eliminando células muertas, grasa y puntos negros acumulados. Disminuye el tamaño de los poros y mejora la textura áspera del rostro.",
        "riesgos": "Se debe evitar baños, saunas y ejercicio tras el tratamiento. Evitar la luz solar intensa durante 2-3 días posteriores.",
        "clausulas": [
            "Se me ha informado los cuidados necesarios posteriores al procedimiento.",
            "Uso de SPF 30 cada 2 horas si se encuentra a la intemperie.",
            "No usar jabones ásperos, exfoliantes o maquillaje pesado inmediatamente."
        ],
        "cuidados_wa": " \n✅ Mantén tu piel muy hidratada.\n✅ Usa protector solar cada 3 horas.\n🚫 No uses exfoliantes ni ácidos por 7 días.\n🚫 Evita el sol directo, piscinas y saunas por 48h.\n🧼 Lava tu cara con un jabón neutro suave."
    },
    "Microneedling (Dermapen)": {
        "desc": "La micropunción es un procedimiento efectivo que va a facilitar la penetración de activos a las capas más profundas de la piel mediante micro-agujas que crean micro-orificios que actúan a modo de túneles.",
        "riesgos": "Las microlesiones producidas favorecen la reparación de la matriz dérmica, estimulando la producción de colágeno y elastina.",
        "clausulas": [
            "Los activos acceden a las capas profundas de manera rápida y efectiva.",
            "Trata daño por exposición solar, arrugas, flacidez y cicatrices de acné o estrías.",
            "Autorizo el control fotográfico pre y post tratamiento con finalidad de control evolutivo."
        ],
        "cuidados_wa": "\n🚫 No apliques maquillaje durante las primeras 24 horas.\n🚫 Evita el sudor excesivo (ejercicio) y el sol directo por 3 días.\n✅ Aplica solo la crema reparadora o suero indicado.\n✅ Usa protector solar SPF 50+ de forma obligatoria."
    },
    "Peeling Químico": {
        "desc": "La finalidad del peeling es promover la renovación celular y así obtener una piel más uniforme y brillante, ayudándonos a contraer poros, controlar lesiones de acné y aclarar manchas.",
        "riesgos": "Escozor, quemazón, rojeces, hipersensibilidad, picazón, desecamiento y descamación. Es lo que se espera ya que la piel reacciona al químico.",
        "clausulas": [
            "Los síntomas pueden durar de 24 a 72 horas o incluso más tiempo según el tipo de piel.",
            "Costras y escamas pueden aparecer y suelen caer tras el reposo.",
            "Riesgo de cambios en la textura de la piel, pérdida de sensibilidad o edema alrededor de los ojos."
        ],
        "cuidados_wa": "\n🚫 *IMPORTANTE:* No arranques las pieles que se estén descamando.\n✅ Hidratación extrema con la crema recomendada.\n✅ Protector solar cada 2-3 horas sin excepción.\n🚫 Evita fuentes de calor intenso (cocina, vapor, sol)."
    },
    "Plasma Rico en Plaquetas": {
        "desc": "Consiste en la aplicación de PRP local (intradérmica, subdérmica o tópica). Se realiza una extracción sanguínea previa que se centrifuga para separar el plasma con plaquetas.",
        "riesgos": "Método seguro por ser autólogo. No existe posibilidad de reacciones inmunológicas. Se realiza bajo estrictas condiciones de asepsia.",
        "clausulas": [
            "La fracción de plasma es activada con cloruro de calcio al 10%.",
            "La aplicación minimiza el riesgo de contaminación e infección.",
            "Responsabilidad del paciente informar sobre su estado de salud física y enfermedades conocidas."
        ],
        "cuidados_wa": "\n🚫 No laves tu cara ni apliques cremas hasta mañana.\n🚫 Evita el ejercicio y el sol directo por 24 horas.\n✅ Bebe abundante agua para mejorar los resultados.\n🚫 No tomes aspirinas o antiinflamatorios si no es necesario."
    },
    "Fibroblast en Párpados": {
        "desc": "Procedimiento de retracción cutánea mediante arco de plasma. Genera micro-carbonizaciones controladas para tensar el tejido y tratar la flacidez sin cirugía.",
        "riesgos": "Inflamación marcada (edema) y formación de costras que caen entre el día 5 y 10.",
        "clausulas": [
            "No retirar las costras manualmente para evitar manchas o cicatrices.",
            "Mantener la zona seca y sin maquillaje hasta la caída total de las costras.",
            "El resultado final se aprecia completamente a las 8-12 semanas."
        ],
        "cuidados_wa": "\n🚫 No mojes la zona tratada las primeras 48 horas.\n✅ Deja que las costras caigan solas (no las toques).\n✅ Usa gafas de sol oscuras al salir.\n✅ Aplica el antiséptico indicado con un hisopo limpio."
    },
    "Tratamiento Pieles Acneicas": {
        "desc": "Protocolo para controlar lesiones de acné, promover la renovación celular y controlar la proliferación bacteriana en la piel.",
        "riesgos": "Descamación, sequedad y posible brote de purga inicial durante la regeneración.",
        "clausulas": [
            "No manipular ni extraer lesiones en casa para evitar infecciones.",
            "Los activos pueden causar escozor tolerable durante la aplicación.",
            "Es responsabilidad del paciente informar sobre su salud y hábitos de higiene."
        ],
        "cuidados_wa": "\n🚫 No toques ni pellizques los granitos.\n✅ Cambia la funda de tu almohada hoy mismo.\n✅ Lava tu rostro solo con el dermolimpiador indicado.\n✅ Usa protector solar 'Oil-Free' o toque seco."
    },
    "Radiofrecuencia Facial": {
        "desc": "Uso de ondas electromagnéticas para calentar la dermis profunda y estimular la producción de nuevo colágeno y elastina.",
        "riesgos": "Eritema leve y sensación de calor interno pasajero tras la sesión.",
        "clausulas": [
            "No poseer implantes metálicos, marcapasos o dispositivos electrónicos.",
            "Los resultados son acumulativos y requieren constancia en las sesiones.",
            "La sensación de calor es necesaria para la eficacia del tensado térmico."
        ],
        "cuidados_wa": "\n✅ Bebe agua para mantener la hidratación térmica de la piel.\n✅ Aplica una mascarilla hidratante fría si sientes mucho calor.\n✅ Puedes retomar tu rutina de maquillaje inmediatamente.\n✅ Usa protector solar como de costumbre."
    },
    "Drenaje Linfático Facial": {
        "desc": "Masaje rítmico manual para favorecer la eliminación de líquidos, edemas y toxinas acumuladas en el rostro.",
        "riesgos": "Aumento de la diuresis (necesidad de orinar) y relajación profunda del sistema nervioso.",
        "clausulas": [
            "Técnica de presión mínima para no colapsar los vasos linfáticos.",
            "Recomendable beber agua para facilitar la depuración del organismo.",
            "No tener procesos infecciosos o febriles activos en el momento del masaje."
        ],
        "cuidados_wa": "\n✅ Bebe al menos 2 litros de agua hoy para eliminar toxinas.\n✅ Evita el consumo de sal en exceso para no retener líquidos.\n✅ Notarás tu rostro más deshinchado y luminoso en las próximas horas.\n🧖‍♀️ ¡Relájate y disfruta del efecto detox!"
    }
}

# --- 4. CLASE PDF LEGAL ---
class ConsentimientoLegal(FPDF):
    def header_logo(self, logo, estetica):
        if logo:
            # Posiciona el logo a la izquierda como en el adjunto
            self.image(logo, 10, 10, 33) 
        self.set_font('Arial', 'B', 12)
        # Nombre del SPA centrado o a la derecha según el logo
        self.cell(0, 10, estetica.upper(), 0, 1, 'R') 
        self.ln(15)

def generar_pdf(datos, logo_file):
    pdf = ConsentimientoLegal()
    pdf.add_page()
    
    # 1. Header (Logo y Nombre SPA)
    tmp_logo = "logo_temp.png"
    if logo_file:
        with open(tmp_logo, "wb") as f: f.write(logo_file.getbuffer())
    pdf.header_logo(tmp_logo if logo_file else None, datos['estetica'])
    
    # 2. Título del Consentimiento (Igual a tus ejemplos)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"CONSENTIMIENTO INFORMADO PARA {datos['servicio'].upper()}", 0, 1, 'C')
    pdf.ln(5)

    # 3. Datos Paciente y Fecha
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, f"Paciente: {datos['paciente']}   |   Fecha: {datetime.date.today()}", 0, 1, 'L')
    pdf.ln(5)

    # 4. Información Técnica (Descripción y Riesgos)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "Información", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, datos['desc'])
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "Riesgos y Efectos Secundarios:", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, datos['riesgos'])
    pdf.ln(5)

    # 5. Cláusulas Específicas de Compromiso
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "Estoy de acuerdo con lo siguiente:", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    clausulas_servicio = SERVICIOS[datos['servicio']].get('clausulas', [])
    for c in clausulas_servicio:
        pdf.multi_cell(0, 5, f"- {c}")
        pdf.ln(1)

    # 6. CIERRE LEGAL (TEXTO EXACTO DE TUS ARCHIVOS)
    pdf.ln(5)
    textos_cierre = [
        "He comprendido las explicaciones que se me han facilitado en un lenguaje claro y sencillo, y el profesional que me ha atendido me ha permitido realizar todas las observaciones y me ha aclarado todas las dudas que le he planteado.",
        "Por ello manifiesto mi conformidad con la información recibida y comprendo el alcance y los riesgos del procedimiento.",
        "Como el profesional que realiza el procedimiento debe estar al tanto de cualquier enfermedad que tenga, he comunicado todas las enfermedades medicas conocidas, y es mi responsabilidad mantenerlo informado sobre el estado de mi salud física.",
        "También se me ha informado debidamente de otros procedimientos alternativos.",
        "Accedo y autorizo a seguir un control fotográfico pre y post tratamientos u otros materiales audiovisuales y gráficos y con la sola finalidad del control evolutivo de mi tratamiento y valoración científica.",
        "Considerando que he sido suficientemente informado/a y aclaradas mis posibles dudas sobre el procedimiento y posibles resultados."
    ]
    
    for t in textos_cierre:
        pdf.multi_cell(0, 5, t)
        pdf.ln(2)

    # 7. ADVERTENCIA FINAL (EN MAYÚSCULAS)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(0, 5, "ES IMPORTANTE QUE LEA CUIDADOSAMENTE LA INFORMACION Y HAYAN SIDO RESPONDIDAS TODAS SUS PREGUNTAS ANTES DE QUE FIRME EL CONSENTIMIENTO.")

    # 8. Espacio para Firmas
    pdf.ln(20)
    pdf.cell(90, 10, "__________________________", 0, 0, 'C')
    pdf.cell(90, 10, "__________________________", 0, 1, 'C')
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(90, 5, "Nombre y Firma de la paciente y fecha", 0, 0, 'C')
    pdf.cell(90, 5, f"Nombre y firma de responsable", 0, 1, 'C')

    if logo_file and os.path.exists(tmp_logo): os.remove(tmp_logo)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 5. INTERFAZ DE USUARIO (SIDEBAR) ---
with st.sidebar:
    st.header("Configuración")
    mi_logo = st.file_uploader("Sube tu Logo Profesional", type=['png', 'jpg', 'jpeg'])
    mi_centro = st.text_input("Nombre de tu Estética", "Mi Estética")
    
    st.divider()
    if not st.session_state["es_pro"]:
        st.write(f"📊 Usos gratuitos: **{st.session_state['usos']} / 5**")
        llave = st.text_input("Ingresar Llave Maestra", type="password")
        if st.button("Activar Versión Full"):
            if llave in CLAVES_PRO:
                st.session_state["es_pro"] = True
                st.success("¡Versión Pro Activada!")
                st.rerun()
            else: st.error("Código incorrecto")
    else:
        st.success("💎 CLIENTE PREMIUM")

# --- 6. LÓGICA DE BLOQUEO POR USOS ---
if st.session_state["usos"] >= 5 and not st.session_state["es_pro"]:
    st.error("⚠️ Has agotado tus 5 fichas de prueba.")
    st.subheader("🚀 Pasa al Nivel Premium")
    st.write("Para obtener tu **Acceso Ilimitado**, sigue estos pasos:")
    
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("💳 Pagar en PayPal", "https://www.paypal.com/ncp/payment/RBUNNAVUXNDRQ")
    with c2:
        msg = urllib.parse.quote("Hola! Ya pagué. Envío comprobante para mi llave.")
        st.link_button("📲 Avisar por WhatsApp", f"https://wa.me/584143451811?text={msg}")
    
    st.stop() 

# --- 7. CUERPO PRINCIPAL ---
st.title("Gestión Estética Profesional")

tab1, tab2 = st.tabs(["📋 Ficha de Consentimiento", "📲 Recomendaciones WhatsApp"])

with tab1:
    st.subheader("Generar Documento Legal")
    col1, col2 = st.columns(2)
    with col1:
        nombre_p = st.text_input("Nombre del Paciente")
        dni_p = st.text_input("DNI / Identificación")
    with col2:
        servicio_p = st.selectbox("Seleccione Tratamiento", list(SERVICIOS.keys()))
    
    st.divider()
    desc_ed = st.text_area("Descripción Técnica:", value=SERVICIOS[servicio_p]["desc"])
    riesgos_ed = st.text_area("Riesgos Informados:", value=SERVICIOS[servicio_p]["riesgos"])

    # LÓGICA DE GENERACIÓN MEJORADA
    if st.button("🚀 PREPARAR DOCUMENTO"):
        if nombre_p and dni_p:
            data_pdf = {
                'paciente': nombre_p, 'dni': dni_p, 'servicio': servicio_p,
                'estetica': mi_centro, 'desc': desc_ed, 'riesgos': riesgos_ed
            }
            try:
                pdf_bytes = generar_pdf(data_pdf, mi_logo)
                
                # Aumentar contador de uso solo si no es PRO
                if not st.session_state["es_pro"]:
                    st.session_state["usos"] += 1
                
                st.success(f"✅ Documento para {nombre_p} listo.")
                st.download_button(
                    label="⬇️ DESCARGAR PDF AHORA", 
                    data=pdf_bytes, 
                    file_name=f"Consentimiento_{nombre_p}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")
        else: 
            st.warning("⚠️ Completa el nombre y DNI del paciente.")

with tab2:
    st.subheader("Envío de Cuidados Posteriores")
    detalles_cuidados = SERVICIOS[servicio_p].get('cuidados_wa', 'Consulte con su profesional.')
    texto_wa = f"TE ACABAS DE HACER UN PROTOCOLO DE *{servicio_p.upper()}* 🧖‍♀️\n\n{detalles_cuidados}"
    st.text_area("Texto para copiar:", value=texto_wa, height=300)
    
    url_final = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"
    st.link_button("🟢 Compartir por WhatsApp", url_final)

with st.sidebar:
    st.divider()
    st.markdown("### 💬 Soporte")
    st.link_button("Contactar a Soporte", "https://wa.me/+584143451811")

from streamlit_gsheets import GSheetsConnection

# Conexión con la base de datos (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

def verificar_y_actualizar_usos(mi_centro):
    # 1. Leer los datos actuales de la nube
    df = conn.read(ttl=0) # ttl=0 para que no use caché y lea en tiempo real
    
    # Buscamos si el centro ya existe en nuestra lista
    if mi_centro in df["identificador"].values:
        usos_actuales = df.loc[df["identificador"] == mi_centro, "usos"].values[0]
    else:
        # Si es nuevo, lo registramos con 0 usos
        usos_actuales = 0
        new_row = pd.DataFrame([{"identificador": mi_centro, "usos": 0}])
        df = pd.concat([df, new_row], ignore_index=True)

    # 2. Verificar límite
    if usos_actuales >= 5:
        return False, usos_actuales
    
    # 3. Si genera el PDF, sumamos 1 uso en la nube
    usos_actuales += 1
    df.loc[df["identificador"] == mi_centro, "usos"] = usos_actuales
    conn.update(data=df) # Guardamos en el Excel de Google
    
    return True, usos_actuales

# --- EN TU INTERFAZ ---
with st.sidebar:
    st.header("Configuración")
    mi_centro = st.text_input("Nombre de tu Estética", "Mi Estética")
    
    # Consultamos a la nube cuántos usos tiene este nombre específicamente
    df_cloud = conn.read(ttl=0)
    if mi_centro in df_cloud["identificador"].values:
        usos_nube = df_cloud.loc[df_cloud["identificador"] == mi_centro, "usos"].values[0]
    else:
        usos_nube = 0

    if not st.session_state.get("es_pro", False):
        st.write(f"📊 Usos registrados: **{usos_nube} / 5**")
        
        if usos_nube >= 5:
            st.error("⚠️ Límite alcanzado para este centro.")
            # Aquí pones tus botones de pago
            st.stop()














