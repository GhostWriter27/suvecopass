import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json

# ==== Inicializar Firebase Admin con credenciales seguras ====
if not firebase_admin._apps:
    try:
        # Carga el JSON como string desde secrets
        sa_json = st.secrets["service_account"]["key_json"]
        # Lo convierte en dict
        sa_info = json.loads(sa_json)

        # Opcional: debug visible en logs de Streamlit Cloud
        print("🔐 Firebase keys:", list(sa_info.keys()))
        print("🔐 private_key empieza con:", sa_info["private_key"][:30])

        # Inicializa Firebase con el dict
        cred = credentials.Certificate(sa_info)
        firebase_admin.initialize_app(cred, {
            "storageBucket": st.secrets["firebase"]["storageBucket"]
        })

        print("✅ Firebase inicializado correctamente.")

    except Exception as e:
        st.error(f"🔥 Error al inicializar Firebase: {e}")
        raise

# ==== Instancias globales ====
db = firestore.client()
bucket = storage.bucket()

# ==== Funciones utilitarias ====
def check_email_exists(email: str) -> bool:
    doc = db.collection("users").document(email).get()
    return doc.exists

def save_qr_record(data: dict) -> None:
    db.collection("qr_records").add(data)

def get_all_qr_records():
    docs = db.collection("qr_records").stream()
    return [doc.to_dict() for doc in docs]