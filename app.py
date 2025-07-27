import os
import streamlit as st
import time
import base64
import requests
import json
from config import firebase_config
from streamlit_lottie import st_lottie

from qr_module import generar_codigo_qr_module
from scan_module import escaneo_qr_module
from firebase_ops import db, bucket

# ==== Configuración general ====
st.set_page_config(page_title="SuvecoPass", layout="wide")

# ==== Forzar siempre visible el icono de sidebar ====
st.markdown(
    """
    <style>
      button[title="Open sidebar"] {
        visibility: visible !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==== Estilos globales ====
css_styles = '''
<style>
  body { font-family: 'Inter', sans-serif; }
  #MainMenu { visibility: hidden; }
  .block-container { padding: 2rem; background: #f0f2f6; }

  .id-card { width:100%; max-width:700px; height:220px; border:2px solid #ccc;
    border-radius:12px; background:#f9f9f9; box-shadow:0 4px 10px rgba(0,0,0,0.1);
    display:flex; overflow:hidden; margin-bottom:40px; }
  .id-photo { flex:0 0 180px; background:#e0e0e0;
    display:flex; align-items:center; justify-content:center; }
  .id-photo img { width:140px; height:180px; object-fit:cover; border:2px solid #ccc; }
  .id-info { flex:1; padding:16px 24px; display:flex;
    flex-direction:column; justify-content:space-around; }
  .id-header { font-size:1.4rem; font-weight:bold; color:#000; margin-bottom:8px; }
  .id-line { font-size:0.95rem; margin-bottom:4px; }
  .id-label { font-weight:bold; color:#444; width:100px; display:inline-block; }
  .id-value { color:#222; }

  .info-card { width:100%; max-width:350px; height:220px; border:2px solid #ccc;
    border-radius:12px; background:#f9f9f9; box-shadow:0 4px 10px rgba(0,0,0,0.1);
    display:flex; align-items:center; justify-content:center; margin-bottom:40px; }
  .info-text { font-size:1.3rem; font-weight:bold; color:#000; text-align:center; }

  .footer { text-align:center; color:#888; font-size:0.85rem; margin-top:40px; }
</style>
'''
st.markdown(css_styles, unsafe_allow_html=True)

# ==== Splash (solo la primera vez) ====
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

# ==== Manejo de sesión (logout) ====
if st.sidebar.button("🚪 Cerrar sesión") and "user_email" in st.session_state:
    st.session_state.pop("user_email", None)
    st.session_state.pop("id_token", None)
    st.rerun()

# ==== Login con Firebase REST ====
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

# ==== Perfil de usuario (primer login) ====
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

# ==== Cargar perfil ====
profile = user_doc.to_dict()
name = f"{profile.get('first_name','')} {profile.get('last_name','')}".strip()
avatar_url = profile.get("avatar_url", "")

# ==== Cargar animación Lottie de confetti ====
def load_lottie_url(url):
    r = requests.get(url)
    return r.json() if r.ok else None

lottie_confetti = load_lottie_url(
    "https://assets9.lottiefiles.com/packages/lf20_touohxv0.json"
)

# ==== Pestañas principales ====
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Inicio", "📤 Generar QR", "📥 Escanear QR", "🔍 Búsqueda manual"
])

# ==== Tab 1: Bienvenida con ID Card y bloque exclusivo ====
with tab1:
    if lottie_confetti:
        st_lottie(lottie_confetti, height=80, key="confetti")
    col1, col2 = st.columns([3, 2])
    with col1:
        img_url = avatar_url or "https://via.placeholder.com/140x180?text=Foto"
        user_id = st.session_state["user_email"].split("@")[0].upper()
        card_html = f"""
        <div class="id-card">
          <div class="id-photo">
            <img src="{img_url}" alt="Foto usuario" />
          </div>
          <div class="id-info">
            <div class="id-header">SUVECOEX 2025</div>
            <div class="id-line"><span class="id-label">Nombre:</span> <span class="id-value">{name}</span></div>
            <div class="id-line"><span class="id-label">Correo:</span> <span class="id-value">{st.session_state["user_email"]}</span></div>
            <div class="id-line"><span class="id-label">Rol:</span> <span class="id-value">Staff autorizado</span></div>
            <div class="id-line"><span class="id-label">ID:</span> <span class="id-value">{user_id}</span></div>
          </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    with col2:
        info_html = """
        <div class="info-card">
          <div class="info-text">App de uso exclusivo para personal autorizado</div>
        </div>
        """
        st.markdown(info_html, unsafe_allow_html=True)

# ==== Tab 2: Generar QR ====
with tab2:
    generar_codigo_qr_module()

# ==== Tab 3: Escanear QR ====
with tab3:
    escaneo_qr_module()

# ==== Tab 4: Búsqueda manual ====
with tab4:
    st.subheader("🔍 Búsqueda manual")
    criterio = st.selectbox("Buscar por", ["Correo", "Nombre", "Cédula"])
    valor = st.text_input(f"Ingrese {criterio.lower()}")
    if st.button("🔍 Buscar"):
        st.info(f"Buscando {valor} por {criterio}")

# ==== Footer ====
st.markdown(
    '<div class="footer">Hecho con ❤️ por el SUVECOEX Team</div>',
    unsafe_allow_html=True
)