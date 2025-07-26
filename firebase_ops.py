import firebase_admin
from firebase_admin import credentials, firestore, storage
from config import firebase_config
from typing import List, Optional

# Inicializar Admin SDK (solo una vez)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": firebase_config["storageBucket"]
    })

# Clientes de Firestore y Storage
db = firestore.client()
bucket = storage.bucket()

def check_email_exists(email: str) -> bool:
    """
    Devuelve True si ya hay un documento en 'qrs' con este email.
    """
    docs = db.collection("qrs").where("email", "==", email).limit(1).stream()
    return any(True for _ in docs)


def save_qr_record(qr_id: str, record: dict) -> None:
    """
    Guarda el diccionario 'record' en Firestore bajo la colección 'qrs' con ID 'qr_id'.
    """
    db.collection("qrs").document(qr_id).set(record)


def get_all_qr_records() -> List[dict]:
    """
    Recupera todos los documentos de 'qrs' y devuelve una lista de sus datos.
    """
    docs = db.collection("qrs").stream()
    return [doc.to_dict() for doc in docs]


def get_qr_record(qr_id: str) -> Optional[dict]:
    """
    Recupera un registro de 'qrs' por su ID.
    Retorna el diccionario si existe, o None si no.
    """
    doc = db.collection("qrs").document(qr_id).get()
    return doc.to_dict() if doc.exists else None


def mark_qr_scanned(qr_id: str, dia: int, scanned_by: str) -> bool:
    """
    Marca escaneado_dia_{dia} = "SI" y scanned_by_dia_{dia} = scanned_by en Firestore.
    """
    campo_flag = f"escaneado_dia_{dia}"
    campo_by   = f"scanned_by_dia_{dia}"
    try:
        db.collection("qrs").document(qr_id).update({campo_flag: "SI", campo_by: scanned_by})
        return True
    except Exception:
        return False


def get_scan_count_for_user(user_email: str, dia: int) -> int:
    """
    Cuenta cuántos documentos en 'qrs' tienen scanned_by_dia_{dia} == user_email.
    """
    campo_by = f"scanned_by_dia_{dia}"
    docs = db.collection("qrs").where(campo_by, "==", user_email).stream()
    return sum(1 for _ in docs)