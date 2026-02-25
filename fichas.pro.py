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
    "Limpieza Facial Profunda": {
        "desc": "Procedimiento de higiene cutánea que incluye exfoliación, extracción de comedones y alta frecuencia para purificar los poros.",
        "riesgos": "Eritema temporal, sensibilidad, posibles brotes por purga de la piel en las siguientes 48 horas.",
        "wa": "✨ *TU PIEL ESTÁ IMPECABLE:*\n✅ Mantén tu funda de almohada limpia hoy.\n✅ No toques ni aprietes las zonas de extracción.\n✅ Evita el maquillaje por las próximas 12-24 horas.\n✅ Lava tu rostro con agua templada o fría.\n✅ Aplica solo la hidratación recomendada.\n🚫 *NO USAR exfoliantes por 3 días.*"
    },
    "Dermapen - Micropunción": {
        "desc": "Inducción de colágeno mediante microagujas que perforan la epidermis para mejorar texturas, marcas de acné y líneas de expresión.",
        "riesgos": "Inflamación leve, pequeñas costras puntuales, enrojecimiento intenso (similar a quemadura solar) por 24-48hs.",
        "wa": "🚨 *PROTOCOLO POST-DERMAPEN:*\n✅ Evita tocarte la cara por completo hoy.\n✅ No sudes (gym, sauna) ni te expongas al sol.\n✅ Higiene con limpiador suave pasadas las 12 horas.\n✅ Hidratación constante con *Crema Reparadora*.\n✅ Uso estricto de Protector Solar cada 3 horas.\n🚫 *NADA DE MAQUILLAJE ni ÁCIDOS por 7 días.*"
    },
    "Peeling Químico": {
        "desc": "Aplicación de agentes químicos para la exfoliación controlada de las capas de la piel, tratando manchas y rejuvenecimiento.",
        "riesgos": "Sensación de quemazón, descamación profusa, sensibilidad extrema y riesgo de manchas si hay exposición solar.",
        "wa": "🚨 *CUIDADOS POST-PEELING:*\n✅ *HIDRATACIÓN:* Crema reparadora cada 4 horas.\n✅ *PROTECCIÓN:* Solar FPS 50+ obligatorio (incluso en casa).\n✅ No arranques las pieles (deja que caigan solas).\n✅ Suspender Retinol o Glicólico por 10 días.\n🚫 *PROHIBIDO EL SOL DIRECTO por 15 días.*"
    },
    "Masajes Reductivos": {
        "desc": "Técnicas manuales y de maderoterapia para remover adiposidad localizada y mejorar el contorno corporal.",
        "riesgos": "Posibles hematomas leves, sensibilidad muscular en la zona tratada y aumento de la diuresis.",
        "wa": "⏳ *RESULTADOS DE TU SESIÓN CORPORAL:*\n✅ Bebe al menos 2 litros de agua para eliminar toxinas.\n✅ Mantén una alimentación baja en grasas y harinas hoy.\n✅ Realiza 30 min de actividad física suave para activar el drenaje.\n✅ Si hay hematomas, aplicar gel de árnica.\n✅ Sé constante con tus sesiones para ver cambios reales."
    }
}

# --- 4. CLASE PDF LEGAL ---
class ConsentimientoLegal(FPDF):
    def header_logo(self, logo, estetica):
        if logo: self.image(logo, 10, 8, 30)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, estetica.upper(), 0, 1, 'R')
        self.ln(10)
def limpiar_texto(texto):
    return texto.encode('latin-1', 'ignore').decode('latin-1')
    
def generar_pdf(datos, logo_file):
    pdf = ConsentimientoLegal()
    pdf.add_page()
    tmp_logo = "logo_temp.png"
    if logo_file:
        with open(tmp_logo, "wb") as f: f.write(logo_file.getbuffer())

    # data = {'paciente': limpiar_texto(p_nombre), ...}
    
    pdf.header_logo(tmp_logo if logo_file else None, datos['estetica'])
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "CONSENTIMIENTO INFORMADO", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, f"Yo, {datos['paciente']}, con identificación {datos['dni']}, declaro estar en pleno uso de mis facultades para autorizar el tratamiento de {datos['servicio']} en {datos['estetica']}.")
    pdf.ln(3)

    secciones = [
        ("Descripción del Servicio:", datos['desc']),
        ("Riesgos y Complicaciones:", datos['riesgos']),
        ("Compromiso del Paciente:", "Acepto seguir estrictamente las pautas y recomendaciones posteriores para maximizar resultados y minimizar riesgos."),
        ("Consentimiento para Fotografías:", "Autorizo la toma de fotografías de mi piel para documentar el progreso del tratamiento."),
        ("Retiro del Consentimiento:", "Soy consciente de que tengo el derecho de retirar mi consentimiento en cualquier momento.")
    ]

    for tit, cont in secciones:
        pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, tit, 0, 1)
        pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 5, cont); pdf.ln(2)

    pdf.ln(15)
    pdf.cell(90, 10, "____________________", 0, 0, 'C'); pdf.cell(90, 10, "____________________", 0, 1, 'C')
    pdf.cell(90, 5, "Firma Paciente", 0, 0, 'C'); pdf.cell(90, 5, f"Firma {datos['estetica']}", 0, 1, 'C')

    if logo_file and os.path.exists(tmp_logo): os.remove(tmp_logo)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ DE USUARIO ---
with st.sidebar:
    st.header("Configuración")
    mi_logo = st.file_uploader("Sube tu Logo Profesional", type=['png', 'jpg', 'jpeg'])
    mi_centro = st.text_input("Nombre de tu Estética", "Nombre de tu estética")
    
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

# LÓGICA DE BLOQUEO
if not st.session_state["es_pro"] and st.session_state["usos"] >= 5:
    st.error("🚨 Has alcanzado el límite de 5 usos gratuitos.")
    st.info("Para seguir utilizando la herramienta, contacta con soporte para adquirir tu suscripción.")
    st.link_button("Adquirir Suscripción", "https://tu-link-de-pago.com")
else:
    tab1, tab2 = st.tabs(["📋 Ficha de Consentimiento", "📲 Recomendaciones WhatsApp"])

    with tab1:
        st.subheader("Generar Documento Legal")
        c1, c2 = st.columns(2)
        with c1:
            nombre_p = st.text_input("Nombre del Paciente")
            dni_p = st.text_input("DNI / Identificación")
        with c2:
            servicio_p = st.selectbox("Seleccione Tratamiento", list(SERVICIOS.keys()))
        
        st.divider()
        desc_ed = st.text_area("Descripción Técnica (Editable):", value=SERVICIOS[servicio_p]["desc"])
        riesgos_ed = st.text_area("Riesgos Informados (Editable):", value=SERVICIOS[servicio_p]["riesgos"])

        if st.button("🚀 GENERAR Y DESCARGAR PDF"):
            if nombre_p and dni_p:
                st.session_state["usos"] += 1
                data_pdf = {
                    'paciente': nombre_p, 'dni': dni_p, 'servicio': servicio_p,
                    'estetica': mi_centro, 'desc': desc_ed, 'riesgos': riesgos_ed
                }
                pdf_bytes = generar_pdf(data_pdf, mi_logo)
                st.download_button(label="⬇️ Haz clic aquí para descargar", data=pdf_bytes, file_name=f"Consentimiento_{nombre_p}.pdf")
            else: st.warning("Por favor, completa los datos del paciente.")

    with tab2:
        st.subheader("Envío de Cuidados Posteriores")
        texto_wa = f"TE ACABAS DE HACER UN PROTOCOLO DE *{servicio_p.upper()}* 🧖‍♀️\n\n{SERVICIOS[servicio_p]['wa']}"
        st.text_area("Texto para copiar:", value=texto_wa, height=300)
        
        url_final = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"

        st.link_button("🟢 Compartir por WhatsApp", url_final)

with st.sidebar:
    st.divider()
    st.markdown("### 💬 ¿Necesitas ayuda o más créditos?")
    st.link_button("Contactar a Soporte", "https://wa.me/+584143451811")

