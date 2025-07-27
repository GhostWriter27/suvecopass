import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

# ==== Inicializar Firebase Admin con credenciales seguras ====
if not firebase_admin._apps:
    # Toma directamente todos los campos de la sección [service_account] de tu secrets.toml
    sa_info = st.secrets["service_account"]
    cred = credentials.Certificate(sa_info)
    firebase_admin.initialize_app(cred, {
        "storageBucket": st.secrets["firebase"]["storageBucket"]
    })

# Instancias globales de Firestore y Storage
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