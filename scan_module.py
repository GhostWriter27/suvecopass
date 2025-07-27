# scan_module.py

import streamlit as st
from firebase_ops import db
import re
from streamlit_qrcode_scanner import qrcode_scanner

def escaneo_qr_module():
    """
    Módulo Streamlit para Escanear QR usando streamlit-qrcode-scanner:
      1) Selección de día (Día 1 / Día 2)
      2) Escáner en tiempo real desde cámara
      3) Decodifica el ID del QR
      4) Verifica y marca ingreso en Firestore
      5) Muestra datos y mensaje de bienvenida
      6) Lleva recuento de escaneos para el día
      7) Botón “Escanear otro QR” para resetear
    """
    st.header("📥 Escaneo de Códigos QR")

    # 1) Día a registrar
    dia = st.selectbox(
        "¿Para qué día registras ingreso?",
        ["Día 1", "Día 2"],
        key="scan_day"
    )

    st.markdown("🔍 **Escanea el QR con tu cámara en tiempo real:**")

    # Reinicio si ya escaneaste
    if st.session_state.get("scan_done", False):
        if st.button("🔄 Escanear otro QR"):
            st.session_state["scan_done"] = False
            for k in ("last_qr_id", "count_dia_1", "count_dia_2"):
                st.session_state.pop(k, None)
        return

    # 2) Escáner desde cámara en vivo
    qr_data = qrcode_scanner(key="qr_live")

    if not qr_data:
        return

    # 3) Extraer el ID SUVECO2025-XXXXXX
    m = re.search(r"SUVECO2025-[A-Z2-9]+", qr_data)
    if not m:
        st.error("❌ El contenido no coincide con el formato esperado.")
        return
    qr_id = m.group(0)

    # 4) Validar en Firestore
    doc = db.collection("qrs").document(qr_id).get()
    if not doc.exists:
        st.error("🚫 Código no encontrado.")
        return

    record = doc.to_dict()
    field = "escaneado_dia_1" if dia == "Día 1" else "escaneado_dia_2"
    if record.get(field) == "SI":
        st.warning(f"⚠️ Ya registraste este código para {dia}.")
        return

    # Marcar ingreso
    db.collection("qrs").document(qr_id).update({field: "SI"})

    # 5) Mostrar bienvenida
    name    = record["name"]
    empresa = record["empresa"]
    phone   = record["phone"]

    st.success(f"✅ ¡{name}!")
    st.write(f"**Empresa:** {empresa}   |   **Teléfono:** {phone}")
    st.markdown(
        f"**¡{name}, bienvenido a SUVECOEX 2025, disfruta del summit donde el comercio exterior conecta, crece y se transforma!**"
    )

    # 6) Contador de escaneos en esta sesión
    counter_key = "count_dia_1" if dia == "Día 1" else "count_dia_2"
    st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
    st.info(f"👤 Has escaneado {st.session_state[counter_key]} vez(ces) en {dia} hoy.")

    # 7) Bloquear hasta reinicio
    st.session_state["scan_done"]   = True
    st.session_state["last_qr_id"]  = qr_id