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
        "info": "Acepto que extensiones de pestañas sean aplicadas y / o eliminadas de mis pestañas. Antes de que mi técnico pueda realizar este procedimiento, entiendo que debo completar este acuerdo y dar mi consentimiento.",
        "riesgos": "Irritación ocular, dolor ocular, comezón en los ojos, malestar, y en casos excepcionales infección ocular.",
        "clausulas": [
            "Entiendo que hay riesgos asociados con la aplicación y/o eliminación de pestañas artificiales.",
            "Las extensiones se aplicarán según determine el técnico para no crear un peso excesivo preservando la salud natural.",
            "Si experimento problemas, me pondré en contacto con mi técnico, retiraré las pestañas y consultaré a un médico.",
            "Los materiales adhesivos pueden alojarse durante o después del procedimiento e irritar mis ojos.",
            "El incumplimiento de las instrucciones de cuidado posterior puede hacer que las extensiones se caigan."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN PROTOCOLO DE *EXTENSIONES DE PESTAÑAS* 🧖‍♀️\n\n✅ No mojarlas las primeras 24-48 horas.\n✅ Cepillarlas diariamente con el cepillo limpio.\n✅ Usar solo productos de limpieza base agua (sin aceites).\n✅ Dormir boca arriba para evitar fricción.\n🚫 No frotar los ojos ni arrancar las extensiones."
    },
    "Limpieza Facial Profunda": {
        "info": "Tratamiento que a través de agua y puntas de diamante realiza una limpieza profunda, eliminando células muertas, grasa y puntos negros. Disminuye poros y mejora la textura áspera.",
        "riesgos": "Se debe evitar baños, saunas y ejercicio tras el tratamiento. Evitar la luz solar intensa.",
        "clausulas": [
            "Evitar la luz solar intensa durante 2-3 días posteriores.",
            "Uso de SPF 30 cada 2 horas si se encuentra a la intemperie.",
            "No usar jabones ásperos, exfoliantes o maquillaje pesado inmediatamente."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UNA *LIMPIEZA FACIAL PROFUNDA* 🧖‍♀️\n\n✅ Mantén tu piel muy hidratada.\n✅ Usa protector solar cada 3 horas.\n🚫 No uses exfoliantes ni ácidos por 7 días.\n🚫 Evita el sol directo, piscinas y saunas por 48h.\n🧼 Lava tu cara con un jabón neutro suave."
    },
    "Microneedling (Dermapen)": {
        "info": "La micropunción facilita la penetración de activos a las capas profundas mediante micro-agujas que crean micro-orificios, estimulando colágeno y elastina.",
        "riesgos": "Eritema, sensibilidad y micro-lesiones propias del proceso de reparación dérmica.",
        "clausulas": [
            "Los activos acceden a las capas profundas de manera rápida y efectiva.",
            "Trata daño solar, arrugas, flacidez y cicatrices de acné.",
            "Autorizo el control fotográfico pre y post tratamiento."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *MICRONEEDLING (DERMAPEN)* 🧖‍♀️\n\n🚫 No apliques maquillaje durante las primeras 24 horas.\n🚫 Evita el sudor excesivo (ejercicio) y el sol directo por 3 días.\n✅ Aplica solo la crema reparadora o suero indicado.\n✅ Usa protector solar SPF 50+ de forma obligatoria."
    },
    "Peeling Químico": {
        "info": "Promueve la renovación celular para obtener una piel uniforme, contraer poros, controlar acné y aclarar manchas.",
        "riesgos": "Escozor, quemazón, rojeces, hipersensibilidad, picazón, desecamiento y descamación.",
        "clausulas": [
            "Los síntomas de descamación pueden durar de 24 a 72 horas o más.",
            "Costras y escamas pueden aparecer y suelen caer tras el reposo.",
            "Posible pérdida de sensibilidad, atrofia o edema alrededor de los ojos."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *PEELING QUÍMICO* 🧖‍♀️\n\n🚫 *IMPORTANTE:* No arranques las pieles que se estén descamando.\n✅ Hidratación extrema con la crema recomendada.\n✅ Protector solar cada 2-3 horas sin excepción.\n🚫 Evita fuentes de calor intenso (cocina, vapor, sol)."
    },
    "Fibroblast en Párpados": {
        "info": "Retracción cutánea mediante arco de plasma. Genera micro-carbonizaciones para tensar el tejido sobrante.",
        "riesgos": "Edema (inflamación) marcado y costras que caen entre el día 5 y 10.",
        "clausulas": [
            "No retirar las costras manualmente para evitar manchas permanentes.",
            "Mantener la zona seca y sin maquillaje hasta la caída total de costras.",
            "El resultado final se aprecia completamente a las 8-12 semanas."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *FIBROBLAST EN PÁRPADOS* 🧖‍♀️\n\n🚫 No mojes la zona tratada las primeras 48 horas.\n✅ Deja que las costras caigan solas (no las toques).\n✅ Usa gafas de sol oscuras al salir.\n✅ Aplica el antiséptico indicado con un hisopo limpio."
    },
    "Tratamiento Pieles Acneicas": {
        "info": "Protocolo para controlar lesiones de acné, promover la renovación celular y controlar la proliferación bacteriana.",
        "riesgos": "Descamación, sequedad y posible brote de purga inicial.",
        "clausulas": [
            "No manipular ni extraer lesiones en casa para evitar cicatrices.",
            "Los activos pueden causar escozor tolerable durante la aplicación.",
            "Los resultados varían según estado hormonal y hábitos de higiene."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *TRATAMIENTO PARA ACNÉ* 🧖‍♀️\n\n🚫 No toques ni pellizques los granitos.\n✅ Cambia la funda de tu almohada hoy mismo.\n✅ Lava tu rostro solo con el dermolimpiador indicado.\n✅ Usa protector solar 'Oil-Free' o toque seco."
    },
    "Plasma Rico en Plaquetas": {
        "info": "Aplicación de PRP obtenido mediante centrifugación de sangre propia activada con cloruro de calcio.",
        "riesgos": "Método seguro por ser autólogo. No existe posibilidad de reacciones inmunológicas.",
        "clausulas": [
            "Obtención y aplicación bajo estrictas condiciones de asepsia.",
            "Responsabilidad del paciente informar sobre su estado de salud física.",
            "Conformidad con el alcance técnico de la infiltración."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *PLASMA RICO EN PLAQUETAS* 🧖‍♀️\n\n🚫 No laves tu cara ni apliques cremas hasta mañana.\n🚫 Evita el ejercicio y el sol directo por 24 horas.\n✅ Bebe abundante agua para mejorar los resultados.\n🚫 No tomes aspirinas o antiinflamatorios si no es necesario."
    },
    "Radiofrecuencia Facial": {
        "info": "Uso de ondas electromagnéticas para calentar la dermis profunda y estimular colágeno.",
        "riesgos": "Eritema leve y sensación de calor interno pasajero.",
        "clausulas": [
            "No poseer implantes metálicos o marcapasos.",
            "Los resultados son acumulativos y requieren varias sesiones.",
            "Sensación de calor necesaria para la eficacia del tensado."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UNA *RADIOFRECUENCIA FACIAL* 🧖‍♀️\n\n✅ Bebe agua para mantener la hidratación térmica de la piel.\n✅ Aplica una mascarilla hidratante fría si sientes mucho calor.\n✅ Puedes retomar tu rutina de maquillaje inmediatamente.\n✅ Usa protector solar como de costumbre."
    },
    "Drenaje Linfático Facial": {
        "info": "Masaje rítmico para favorecer la eliminación de líquidos y toxinas del rostro.",
        "riesgos": "Aumento de la diuresis y relajación profunda.",
        "clausulas": [
            "Técnica de presión mínima para no colapsar vasos linfáticos.",
            "Recomendable beber agua para facilitar la depuración.",
            "No tener procesos infecciosos o febriles activos."
        ],
        "cuidados_wa": "TE ACABAS DE HACER UN *DRENAJE LINFÁTICO FACIAL* 🧖‍♀️\n\n✅ Bebe al menos 2 litros de agua hoy para eliminar toxinas.\n✅ Evita el consumo de sal en exceso para no retener líquidos.\n✅ Notarás tu rostro más deshinchado y luminoso en las próximas horas.\n🧖‍♀️ ¡Relájate y disfruta del efecto detox!"
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
    
    # Manejo de logo temporal
    tmp_logo = "logo_temp.png"
    if logo_file:
        with open(tmp_logo, "wb") as f: f.write(logo_file.getbuffer())

    pdf.header_logo(tmp_logo if logo_file else None, datos['estetica'])
    
    # Título Profesional [cite: 2]
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"CONSENTIMIENTO INFORMADO PARA {datos['servicio'].upper()}", 0, 1, 'C')
    pdf.ln(5)

    # Bloque de Información General [cite: 4, 5]
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, f"Paciente: {datos['paciente']}   |   Identificación: {datos['dni']}   |   Fecha: {datetime.date.today()}", 1, 1, 'L')
    pdf.ln(5)

    # Cláusulas de Compromiso y Aceptación (Texto más técnico) [cite: 9, 11, 17, 18]
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "DECLARACIONES Y COMPROMISOS:", 0, 1)
    pdf.set_font('Arial', '', 9)
    
    declaraciones = [
        f"1. Acepto que el procedimiento de {datos['servicio']} sea aplicado siguiendo los protocolos técnicos de seguridad.",
        "2. Entiendo que existen riesgos asociados, incluyendo irritación, malestar o reacciones alérgicas.",
        "3. Me comprometo a contactar al técnico y consultar a un médico por mi cuenta si experimento problemas graves.",
        "4. He comunicado todas mis condiciones médicas conocidas y es mi responsabilidad mantener al profesional informado.",
        "5. Autorizo el control fotográfico pre y post tratamiento con fines de valoración científica y seguimiento evolutivo."
    ]
    
    for item in declaraciones:
        pdf.multi_cell(0, 5, item)
        pdf.ln(1)

    # Detalles Específicos del Servicio
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "DESCRIPCIÓN TÉCNICA:", 0, 1)
    pdf.set_font('Arial', '', 9); pdf.multi_cell(0, 5, datos['desc'])
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "RIESGOS INFORMADOS:", 0, 1)
    pdf.set_font('Arial', '', 9); pdf.multi_cell(0, 5, datos['riesgos'])

    # Advertencia Final [cite: 23]
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(200, 0, 0) # Color rojo para advertencia
    pdf.multi_cell(0, 5, "ES IMPORTANTE QUE LEA CUIDADOSAMENTE ESTA INFORMACIÓN Y HAYA ACLARADO TODAS SUS DUDAS ANTES DE FIRMAR.")
    pdf.set_text_color(0, 0, 0)

    # Firmas [cite: 24, 25]
    pdf.ln(20)
    pdf.cell(90, 10, "__________________________", 0, 0, 'C')
    pdf.cell(90, 10, "__________________________", 0, 1, 'C')
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(90, 5, "Firma del Paciente", 0, 0, 'C')
    pdf.cell(90, 5, "Firma del Responsable / Técnico", 0, 1, 'C')

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








