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
        "cuidados_wa": """✨ *TU PIEL ESTÁ IMPECABLE:*
✅ Mantén tu funda de almohada limpia hoy.
✅ No toques ni aprietes las zonas de extracción.
✅ Evita el maquillaje por las próximas 12-24 horas.
✅ Lava tu rostro con agua templada o fría.
✅ Aplica solo la hidratación recomendada.
🚫 *NO USAR exfoliantes por 3 días.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Microneedling (Dermapen)": {
        "desc": "Inducción de colágeno mediante microagujas que perforan la epidermis para mejorar texturas, marcas de acné y líneas de expresión.",
        "riesgos": "Inflamación leve, pequeñas costras puntuales, enrojecimiento intenso (similar a quemadura solar) por 24-48hs.",
        "cuidados_wa": """🚨 *PROTOCOLO POST-DERMAPEN:*
✅ Evita tocarte la cara por completo hoy.
✅ No sudes (gym, sauna) ni te expongas al sol.
✅ Higiene con limpiador suave pasadas las 12 horas.
✅ Hidratación constante con *Crema Reparadora*.
✅ Uso estricto de Protector Solar cada 3 horas.
🚫 *NADA DE MAQUILLAJE ni ÁCIDOS por 7 días.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Peeling Químico": {
        "desc": "Aplicación de agentes químicos para la exfoliación controlada de las capas de la piel, tratando manchas y rejuvenecimiento.",
        "riesgos": "Sensación de quemazón, descamación profusa, sensibilidad extrema y riesgo de manchas si hay exposición solar.",
        "cuidados_wa": """🚨 *CUIDADOS POST-PEELING:*
✅ *HIDRATACIÓN:* Crema reparadora cada 4 horas.
✅ *PROTECCIÓN:* Solar FPS 50+ obligatorio (incluso en casa).
✅ No arranques las pieles (deja que caigan solas).
✅ Suspender Retinol o Glicólico por 10 días.
🚫 *PROHIBIDO EL SOL DIRECTO por 15 días.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Fibroblast en Párpados": {
        "desc": "Generación de arco de plasma para retracción de tejido en párpados (blefaroplastia no quirúrgica).",
        "riesgos": "Edema (inflamación) marcado los primeros 3 días, formación de costras de carbono y sensibilidad.",
        "cuidados_wa": """👁️ *CUIDADOS DE FIBROBLAST:*
✅ Mantén el área tratada seca y limpia.
✅ *IMPORTANTE:* Deja que las costras caigan solas, NO las arranques.
✅ Usa gafas de sol oscuras para protección UV.
✅ Duerme con la cabeza elevada para reducir la inflamación.
🚫 *NO aplicar maquillaje ni cremas hasta que las costras caigan.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Tratamiento Pieles Acneicas": {
        "desc": "Protocolo de control sebáceo y desinfección para reducir lesiones activas de acné y prevenir cicatrices.",
        "riesgos": "Resequedad, descamación leve y fotosensibilidad por activos bactericidas.",
        "cuidados_wa": """🧼 *PROTOCOLO CONTROL ACNÉ:*
✅ Lava tu rostro con el limpiador indicado mañana y noche.
✅ *NO manipules las lesiones:* puedes causar manchas o cicatrices.
✅ Cambia tu toalla de rostro diariamente (o usa toallas de papel).
✅ Usa hidratante tipo Gel o 'Oil-Free'.
🚫 *EVITA el sol directo y el calor extremo.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Plasma Rico en Plaquetas (PRP)": {
        "desc": "Bioestimulación mediante factores de crecimiento autólogos para mejorar la calidad y tensión de la piel.",
        "riesgos": "Pequeños hematomas en puntos de inyección e inflamación local leve.",
        "cuidados_wa": """💉 *POST-PLASMA (PRP):*
✅ No toques ni masajees las zonas de inyección hoy.
✅ Evita el ejercicio físico y el sudor por 24 horas.
✅ No apliques maquillaje ni cremas pesadas el día de hoy.
✅ Si sientes inflamación, aplica compresas frías con suavidad.
🚫 *EVITA el consumo de alcohol y tabaco hoy.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Drenaje Linfático Facial": {
        "desc": "Masaje rítmico manual para estimular la eliminación de toxinas y reducir el edema facial.",
        "riesgos": "Aumento de la diuresis (ganas de orinar) y relajación muscular.",
        "cuidados_wa": """💆‍♀️ *POST-DRENAJE FACIAL:*
✅ Bebe mucha agua para ayudar a eliminar las toxinas.
✅ Evita el consumo excesivo de sal el día de hoy.
✅ Mantén tu rostro fresco y evita productos pesados.
✅ Descansa y permite que tu sistema linfático trabaje.

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Radiofrecuencia Facial": {
        "desc": "Transferencia de energía electromagnética para generar calor dérmico y estimular la síntesis de colágeno.",
        "riesgos": "Eritema leve que desaparece en pocas horas y sensación de calor interno.",
        "cuidados_wa": """🔥 *POST-RADIOFRECUENCIA:*
✅ Mantén tu piel profundamente hidratada.
✅ No laves tu cara con agua muy caliente hoy.
✅ Bebe abundante agua para favorecer la regeneración celular.
✅ Usa protector solar FPS 50+ sin falta.
🚫 *EVITA saunas o baños de vapor hoy.*

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
    },
    "Masajes Reductivos": {
        "desc": "Técnicas manuales y de maderoterapia para remover adiposidad localizada y mejorar el contorno corporal.",
        "riesgos": "Posibles hematomas leves, sensibilidad muscular en la zona tratada y aumento de la diuresis.",
        "cuidados_wa": """⏳ *RESULTADOS DE TU SESIÓN CORPORAL:*
✅ Bebe al menos 2 litros de agua para eliminar toxinas.
✅ Mantén una alimentación baja en grasas y harinas hoy.
✅ Realiza 30 min de actividad física suave para activar el drenaje.
✅ Si hay hematomas, aplicar gel de árnica.
✅ Sé constante con tus sesiones para ver cambios reales.

💬 *Cualquier duda o consulta, puedes escribir directamente a tu Cosmetólogo/Cosmiatra.*"""
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
if st.session_state["usos"] >= 5 and not st.session_state["autenticado"]:
    st.error("⚠️ Has agotado tus 5 fichas de prueba.")
    st.write("Para seguir generando fichas ilimitadas y profesionalizar tu estética, adquiere tu suscripción:")
    st.link_button("💳 Pagar Suscripción en PayPal", "https://www.paypal.com/ncp/payment/RBUNNAVUXNDRQ")
    st.stop() # Esto detiene la app para que no puedan seguir
    
    # Botón de pago directo a PayPal
st.sidebar.divider() # Añade una línea divisoria para separar
st.sidebar.markdown("### 💎 Acceso Premium")
st.sidebar.link_button(
    "🚀 Adquirir Suscripción Ilimitada", 
    "https://www.paypal.com/ncp/payment/RBUNNAVUXNDRQ",
    use_container_width=True, # Hace que el botón ocupe todo el ancho de la barra
    type="primary" # Lo pone en color de resalte (generalmente rojo o naranja según tu tema)
)
st.sidebar.caption("Pago seguro procesado por PayPal")
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
        
        # CAMBIO CLAVE: Usamos 'cuidados_wa' en lugar de 'wa'
        # Usamos .get() para evitar que la app se caiga si falta algún dato
        detalles_cuidados = SERVICIOS[servicio_p].get('cuidados_wa', 'Consulte con su profesional.')
        
        texto_wa = f"TE ACABAS DE HACER UN PROTOCOLO DE *{servicio_p.upper()}* 🧖‍♀️\n\n{detalles_cuidados}"
        
        st.text_area("Texto para copiar:", value=texto_wa, height=300)
        
        url_final = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"
        st.link_button("🟢 Compartir por WhatsApp", url_final)

with st.sidebar:
    st.divider()
    st.markdown("### 💬 ¿Necesitas ayuda o más créditos?")
    st.link_button("Contactar a Soporte", "https://wa.me/+584143451811")





