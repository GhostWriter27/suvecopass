import json
import streamlit as st
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

# ==== Inicializar Firebase Admin con credenciales seguras ====
if not firebase_admin._apps:
    # Carga el JSON de la cuenta de servicio desde los secrets de Streamlit
    sa_json = st.secrets["service_account"]["key_json"]
    sa_info = json.loads(sa_json)
    cred = credentials.Certificate(sa_info)
    firebase_admin.initialize_app(cred, {
        "storageBucket": st.secrets["firebase"]["storageBucket"]
    })

# Instanciar Firestore y Storage globales
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