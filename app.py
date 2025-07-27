import os
import streamlit as st
import time
import base64
import requests
from config import firebase_config
from streamlit_lottie import st_lottie

from qr_module import generar_codigo_qr_module
from scan_module import escaneo_qr_module
from firebase_ops import db, bucket

# ==== Configuración general ====
st.set_page_config(page_title="SuvecoPass", layout="centered")

# ==== Estilos globales optimizados ====
st.markdown("""
<style>
  body {
    font-family: 'Inter', sans-serif;
    background: #fff;
  }

  #MainMenu, header, footer {
    visibility: hidden;
  }

  .block-container {
    padding: 1rem;
  }

  label, .stTextInput > label, .stSelectbox > label, .stTextArea > label {
    color: #000 !important;
    font-weight: bold;
  }

  input, select, textarea {
    color: #000 !important;
  }

  h1, h2, h3, h4, h5 {
    color: #000 !important;
  }

  video {
    width: 100vw !important;
    max-width: 100% !important;
    height: auto !important;
    display: block;
    margin: auto;
    z-index: 1;
  }

  canvas {
    display: none !important;
  }

  .id-card, .info-card {
    width: 100%;
    max-width: 600px;
    height: auto;
    border: 2px solid #ccc;
    border-radius: 12px;
    background: #f9f9f9;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    margin: 20px auto;
    display: flex;
    flex-direction: column;
    text-align: center;
    padding: 1rem;
  }

  .id-photo img {
    width: 140px;
    height: 180px;
    object-fit: cover;
    border: 2px solid #ccc;
    margin: 0 auto;
    display: block;
  }

  .id-header {
    font-size: 1.4rem;
    font-weight: bold;
    color: #000;
    margin-bottom: 8px;
  }

  .id-line {
    font-size: 1rem;
    margin-bottom: 4px;
  }

  .id-label {
    font-weight: bold;
    color: #444;
  }

  .id-value {
    color: #222;
  }

  .info-text {
    font-size: 1.1rem;
    font-weight: bold;
    color: #000;
  }

  .footer {
    text-align: center;
    color: #888;
    font-size: 0.85rem;
    margin-top: 30px;
  }

  button[title="Open sidebar"] {
    visibility: visible !important;
  }
</style>
""", unsafe_allow_html=True)

# ==== Splash ====
def get_base64_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

if "splash_shown" not in st.session_state:
    splash = st.empty()
    gif_b64 = get_base64_file(os.path.join(os.path.dirname(__file__), "splash.gif"))
    splash.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:center;
            height:100vh; background-color:#e0e0e0; margin:-1rem;">
          <img src="data:image/gif;base64,{gif_b64}" style="max-width:80%; height:auto;" />
        </div>
        """,
        unsafe_allow_html=True
    )
    time.sleep(4)
    splash.empty()
    st.session_state.splash_shown = True

# ==== Logout ====
if st.sidebar.button("🚪 Cerrar sesión") and "user_email" in st.session_state:
    st.session_state.pop("user_email", None)
    st.session_state.pop("id_token", None)
    st.rerun()

# ==== Login ====
if "user_email" not in st.session_state:
    st.sidebar.header("🔐 Iniciar sesión")
    email = st.sidebar.text_input("Email")
    pwd = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        payload = {"email": email, "password": pwd, "returnSecureToken": True}
        url = (
            "https://identitytoolkit.googleapis.com/v1/"
            f"accounts:signInWithPassword?key={firebase_config['apiKey']}"
        )
        r = requests.post(url, data=payload)
        if r.ok:
            st.session_state.user_email = email
            st.session_state.id_token = r.json()["idToken"]
            st.rerun()
        else:
            err = r.json().get("error", {}).get("message", "UNKNOWN_ERROR")
            st.sidebar.error(f"📛 {err}")
    st.stop()

# ==== Crear perfil ====
user_doc_ref = db.collection("users").document(st.session_state["user_email"])
user_doc = user_doc_ref.get()
if not user_doc.exists:
    st.sidebar.header("📝 Completa tu perfil")
    first = st.sidebar.text_input("Nombre")
    last = st.sidebar.text_input("Apellidos")
    photo_file = st.sidebar.file_uploader("Foto de perfil (opcional)", type=["png","jpg","jpeg"])
    photo_cam = st.sidebar.camera_input("Tomar foto (opcional)")
    if st.sidebar.button("Guardar perfil"):
        data = {"first_name": first, "last_name": last}
        img = photo_file or photo_cam
        if img:
            blob = bucket.blob(f"avatars/{st.session_state['user_email']}.png")
            blob.upload_from_string(img.getvalue(), content_type=img.type)
            blob.make_public()
            data["avatar_url"] = blob.public_url
        user_doc_ref.set(data)
        st.rerun()
    st.stop()

# ==== Perfil cargado ====
profile = user_doc.to_dict()
name = f"{profile.get('first_name','')} {profile.get('last_name','')}".strip()
avatar_url = profile.get("avatar_url", "")

# ==== Cargar animación Lottie ====
def load_lottie_url(url):
    r = requests.get(url)
    return r.json() if r.ok else None

lottie_confetti = load_lottie_url(
    "https://assets9.lottiefiles.com/packages/lf20_touohxv0.json"
)

# ==== Tabs ====
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Inicio", "📤 Generar QR", "📥 Escanear QR", "🔍 Búsqueda manual"
])

# ==== Tab 1: Inicio ====
with tab1:
    if lottie_confetti:
        st_lottie(lottie_confetti, height=80, key="confetti")
    st.markdown(f"""
    <div class="id-photo">
      <img src="{avatar_url or 'https://via.placeholder.com/140x180?text=Foto'}" alt="Foto">
    </div>
    <div class="id-card">
      <div class="id-header">SUVECOEX 2025</div>
      <div class="id-line"><span class="id-label">Nombre:</span> {name}</div>
      <div class="id-line"><span class="id-label">Correo:</span> {st.session_state['user_email']}</div>
      <div class="id-line"><span class="id-label">Rol:</span> Staff autorizado</div>
    </div>
    <div class="info-card">
      <div class="info-text">App de uso exclusivo para personal autorizado</div>
    </div>
    """, unsafe_allow_html=True)

# ==== Tab 2: Generar QR ====
with tab2:
    generar_codigo_qr_module()

# ==== Tab 3: Escanear QR ====
with tab3:
    escaneo_qr_module()

# ==== Tab 4: Búsqueda manual ====
with tab4:
    st.info("🔧 Módulo de búsqueda manual en desarrollo.")

# ==== Footer ====
st.markdown('<div class="footer">Hecho con ❤️ por el SUVECOEX Team</div>', unsafe_allow_html=True)