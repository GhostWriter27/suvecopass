# scan_module.py

import streamlit as st
from firebase_ops import db
import re
from streamlit_qrcode_scanner import qrcode_scanner

def escaneo_qr_module():
    """
    Escaneo QR responsivo usando streamlit-qrcode-scanner con Firestore.
    """
    st.header("📥 Escaneo de Códigos QR")

    # Día del registro
    dia = st.selectbox(
        "¿Para qué día registras ingreso?",
        ["Día 1", "Día 2"],
        key="scan_day"
    )

    # Si ya escaneaste, botón de reinicio
    if st.session_state.get("scan_done", False):
        if st.button("🔄 Escanear otro QR"):
            st.session_state["scan_done"] = False
            for k in ("last_qr_id", "count_dia_1", "count_dia_2"):
                st.session_state.pop(k, None)
        return

    st.markdown("📲 **Apunta la cámara al código QR** y espera unos segundos.")

    qr_data = None
    try:
        with st.container():
            qr_data = qrcode_scanner(key="qr_live")
    except Exception as e:
        st.error("❌ No se pudo acceder a la cámara.")
        st.info("Activa los permisos de cámara o cambia de navegador/dispositivo.")
        st.stop()

    if not qr_data:
        st.info("📷 Esperando escaneo...")
        return

    # Validar formato de ID
    m = re.search(r"SUVECO2025-[A-Z2-9]+", qr_data)
    if not m:
        st.error("❌ El contenido no coincide con el formato esperado.")
        return
    qr_id = m.group(0)

    # Buscar en Firestore
    doc = db.collection("qrs").document(qr_id).get()
    if not doc.exists:
        st.error("🚫 Código no encontrado.")
        return

    record = doc.to_dict()
    field = "escaneado_dia_1" if dia == "Día 1" else "escaneado_dia_2"

    if record.get(field) == "SI":
        st.warning(f"⚠️ Ya registraste este código para {dia}.")
        return

    # Marcar como escaneado
    db.collection("qrs").document(qr_id).update({field: "SI"})

    # Mostrar bienvenida
    name = record.get("name", "")
    empresa = record.get("empresa", "")
    phone = record.get("phone", "")

    st.success(f"✅ ¡{name} ha sido registrado exitosamente!")
    st.write(f"**Empresa:** {empresa}   |   **Teléfono:** {phone}")
    st.markdown(
        f"**¡{name}, bienvenido a SUVECOEX 2025, donde el comercio exterior conecta, crece y se transforma!**"
    )

    # Contador de escaneos
    counter_key = "count_dia_1" if dia == "Día 1" else "count_dia_2"
    st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
    st.info(f"👤 Has escaneado {st.session_state[counter_key]} vez(ces) en {dia} hoy.")

    # Bloqueo hasta reinicio
    st.session_state["scan_done"]  = True
    st.session_state["last_qr_id"] = qr_id