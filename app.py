import os
import streamlit as st
import time
import base64
import requests
from config import firebase_config
from streamlit_lottie import st_lottie

from qr_module import generar_codigo_qr_module
from scan_module import escaneo_qr_module
from manual_search_module import busqueda_manual_module

# ==== Configuración general ====
st.set_page_config(page_title="SuvecoPass", layout="centered")

# ==== CSS global unificado ====
st.markdown("""
<style>
  :root { --gutter: 1rem; --max-w: 90vw; }

  /* Contenedor central */
  .container { width: var(--max-w); max-width: 1200px; margin: 0 auto; }

  /* Card genérica */
  .card {
    background: #ffffff;
    border-radius: .75rem;
    padding: var(--gutter);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin: var(--gutter) auto;
  }

  /* ID Card */
  .id-card {
    display: flex; overflow: hidden;
    max-width: 700px; height: 220px;
  }
  .id-photo {
    flex: 0 0 180px; background: #e0e0e0;
    display: flex; align-items: center; justify-content: center;
  }
  .id-photo img {
    width: 140px; height: 180px;
    object-fit: cover; border: 2px solid #ccc;
  }
  .id-info {
    flex: 1; padding: 16px 24px;
    display: flex; flex-direction: column; justify-content: space-around;
  }
  .id-header { font-size: 1.4rem; font-weight: bold; margin-bottom: 8px; }
  .id-line { font-size: 0.95rem; margin-bottom: 4px; }
  .id-label { font-weight: bold; width: 80px; display: inline-block; }

  /* Info Card */
  .info-card {
    display: flex; align-items: center; justify-content: center;
    max-width: 350px; height: 220px;
  }
  .info-text { font-size: 1.3rem; font-weight: bold; text-align: center; }

  /* INPUTs y TEXTAREA */
  input, textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
  }

  /* STREAMLIT SELECTBOX & DATEINPUT */
  div[data-baseweb="select"] > div:first-child,
  div[data-testid="stSelectbox"] div[role="combobox"] > div,
  div[data-testid="stSelectbox"] div[role="combobox"],
  div[data-testid="stDateInput"] input,
  div[data-testid="stDateInput"] .css-1occu11 {
    background-color: #ffffff !important;
    color: #000000 !important;
  }

  /* También las listas desplegables */
  div[data-baseweb="select"] ul,
  div[role="listbox"] > div {
    background-color: #ffffff !important;
    color: #000000 !important;
  }

  /* Botones genéricos */
  .btn {
    display: inline-block; width: 100%; padding: .75rem; font-size: 1rem;
    border: none; border-radius: .5rem; text-align: center; cursor: pointer;
  }
  .btn-primary { background-color: #007bff; color: white; }
  .btn-secondary { background-color: #6c757d; color: white; }

  /* Sidebar siempre visible */
  button[title="Open sidebar"] { visibility: visible !important; }

  /* Tweaks Streamlit */
  body { font-family: 'Inter', sans-serif; }
  #MainMenu { visibility: hidden; }
  .block-container { padding: 2rem; background: #f0f2f6; }

  /* Footer */
  .footer {
    text-align: center; color: #888; font-size: 0.85rem; margin-top: 2rem;
  }
</style>
""", unsafe_allow_html=True)

# ==== Inicializar Firebase Admin ====
if not firebase_admin._apps:
    key_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred, {
        "storageBucket": firebase_config["storageBucket"]
    })
db = firestore.client()
bucket = storage.bucket()

# ==== Splash (solo la primera vez) ====
if "splash_shown" not in st.session_state:
    placeholder = st.empty()
    gif_path = os.path.join(os.path.dirname(__file__), "splash.gif")
    with open(gif_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    placeholder.markdown(f"""
      <div style="display:flex;justify-content:center;align-items:center;
                  height:100vh;background:#e0e0e0;margin:0;">
        <img src="data:image/gif;base64,{b64}" style="max-width:80%;height:auto;" />
      </div>
    """, unsafe_allow_html=True)
    time.sleep(4)
    placeholder.empty()
    st.session_state.splash_shown = True

# ==== Sidebar: login o menú principal ====
if "user_email" not in st.session_state:
    st.sidebar.header("🔐 Iniciar sesión")
    email = st.sidebar.text_input("Email")
    pwd   = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        payload = {"email": email, "password": pwd, "returnSecureToken": True}
        url = ("https://identitytoolkit.googleapis.com/v1/"
               f"accounts:signInWithPassword?key={firebase_config['apiKey']}")
        r = requests.post(url, data=payload)
        if r.ok:
            st.session_state.user_email = email
            st.session_state.id_token  = r.json()["idToken"]
            st.experimental_rerun()
        else:
            st.sidebar.error(f"📛 {r.json().get('error',{}).get('message','ERROR')}")
    st.stop()
else:
    user_doc = db.collection("users").document(st.session_state["user_email"]).get()
    if not user_doc.exists:
        st.sidebar.header("📝 Completa tu perfil")
        first      = st.sidebar.text_input("Nombre")
        last       = st.sidebar.text_input("Apellidos")
        photo_file = st.sidebar.file_uploader("Foto de perfil", type=["png","jpg","jpeg"])
        photo_cam  = st.sidebar.camera_input("Tomar foto")
        if st.sidebar.button("Guardar perfil"):
            data = {"first_name": first, "last_name": last}
            img  = photo_file or photo_cam
            if img:
                blob = bucket.blob(f"avatars/{st.session_state['user_email']}.png")
                blob.upload_from_string(img.getvalue(), content_type=img.type)
                blob.make_public()
                data["avatar_url"] = blob.public_url
            user_doc.reference.set(data)
            st.experimental_rerun()
        st.stop()

    profile = user_doc.to_dict()
    name    = f"{profile.get('first_name','')} {profile.get('last_name','')}".strip()

    st.sidebar.markdown(f"## Hola, {name} 👋")
    choice = st.sidebar.selectbox(
        "Selecciona módulo",
        ["Inicio", "Generar QR", "Escanear QR", "Búsqueda manual"]
    )
    if st.sidebar.button("🚪 Cerrar sesión"):
        for k in ("user_email","id_token"):
            st.session_state.pop(k, None)
        st.experimental_rerun()

# ==== Carga Lottie confetti ====
def load_lottie_url(url):
    r = requests.get(url)
    return r.json() if r.ok else None
lottie_confetti = load_lottie_url(
    "https://assets9.lottiefiles.com/packages/lf20_touohxv0.json")

# ==== Contenedor principal ====
st.markdown("<div class='container'>", unsafe_allow_html=True)

if choice == "Inicio":
    if lottie_confetti:
        st.markdown("<div class='card' style='display:flex;justify-content:center;'>",
                    unsafe_allow_html=True)
        st_lottie(lottie_confetti, height=80, key="confetti")
        st.markdown("</div>", unsafe_allow_html=True)

    cols = st.columns([3, 2], gap="large")
    with cols[0]:
        st.markdown(f"""
          <div class="card id-card">
            <div class="id-photo">
              <img src="{profile.get('avatar_url',
                    'https://via.placeholder.com/140x180?text=Foto')}"
                   alt="Foto usuario" />
            </div>
            <div class="id-info">
              <div class="id-header">SUVECOEX 2025</div>
              <div class="id-line">
                <span class="id-label">Nombre:</span>
                <span class="id-value">{name}</span>
              </div>
              <div class="id-line">
                <span class="id-label">Correo:</span>
                <span class="id-value">{st.session_state['user_email']}</span>
              </div>
              <div class="id-line">
                <span class="id-label">Rol:</span>
                <span class="id-value">Staff autorizado</span>
              </div>
              <div class="id-line">
                <span class="id-label">ID:</span>
                <span class="id-value">
                  {st.session_state['user_email'].split('@')[0].upper()}
                </span>
              </div>
            </div>
          </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
          <div class="card info-card">
            <div class="info-text">
              App de uso exclusivo para personal autorizado
            </div>
          </div>
        """, unsafe_allow_html=True)

elif choice == "Generar QR":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    generar_codigo_qr_module()
    st.markdown("</div>", unsafe_allow_html=True)

elif choice == "Escanear QR":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    escaneo_qr_module()
    st.markdown("</div>", unsafe_allow_html=True)

elif choice == "Búsqueda manual":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    busqueda_manual_module()
    st.markdown("</div>", unsafe_allow_html=True)

# ==== Footer ====
st.markdown("""
  <div class="card footer">
    Hecho con ❤️ por el SUVECOEX Team
  </div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
