import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json

# ==== Inicializar Firebase Admin con reparación de PEM ====
if not firebase_admin._apps:
    try:
        sa_json = st.secrets["service_account"]["key_json"]
        sa_info = json.loads(sa_json)

        # 🔧 Reparar: convertir '\\n' a '\n' en la clave privada
        sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(sa_info)
        firebase_admin.initialize_app(cred, {
            "storageBucket": st.secrets["firebase"]["storageBucket"]
        })

        print("✅ Firebase inicializado.")

    except Exception as e:
        st.error(f"🔥 Error al inicializar Firebase: {e}")
        raise

db = firestore.client()
bucket = storage.bucket()

def check_email_exists(email: str) -> bool:
    doc = db.collection("users").document(email).get()
    return doc.exists

def save_qr_record(data: dict) -> None:
    db.collection("qr_records").add(data)

def get_all_qr_records():
    docs = db.collection("qr_records").stream()
    return [doc.to_dict() for doc in docs]
