# scan_module.py

import re
import streamlit as st
from firebase_ops import db
from streamlit_qrcode_scanner import qrcode_scanner

def escaneo_qr_module():
    """
    Módulo Streamlit para Escanear QR EN VIVO con streamlit-qrcode-scanner:
      1) Selección de día (Día 1 / Día 2)
      2) qrcode_scanner() abre la cámara y detecta el QR en vivo
      3) Decodifica el texto del QR
      4) Verifica y marca ingreso en Firestore
      5) Muestra datos y mensaje de bienvenida
      6) Lleva recuento de escaneos para el día
      7) Botón “Escanear otro QR” para resetear
    """
    st.header("📥 Escaneo de Códigos QR")

    # Día del registro
    dia = st.selectbox(
        "¿Para qué día registras ingreso?",
        ["Día 1", "Día 2"],
        key="scan_day"
    )

    st.markdown("🔍 **Apunta tu cámara al QR para escanear en vivo:**")

    # 2) Cámara en vivo + detección automática
    data = qrcode_scanner(key="qr_scanner")

    # 9) Reinicio si ya escaneaste
    if st.session_state.get("scan_done", False):
        if st.button("🔄 Escanear otro QR"):
            for k in ("scan_done", "last_qr_id", "count_dia_1", "count_dia_2"):
                st.session_state.pop(k, None)
        st.info("Presiona el botón para escanear otro QR.")
        return

    # 3) No seguimos hasta tener datos
    if not data:
        return

    # 4) El componente ya nos da el texto, lo analizamos
    m = re.search(r"SUVECO2025-[A-Z2-9]+", data)
    if not m:
        st.error("❌ El contenido no coincide con el formato esperado.")
        return
    qr_id = m.group(0)

    # 5) Validar en Firestore
    doc = db.collection("qrs").document(qr_id).get()
    if not doc.exists:
        st.error("🚫 Código no encontrado.")
        return

    record = doc.to_dict()
    field = "escaneado_dia_1" if dia == "Día 1" else "escaneado_dia_2"

    if record.get(field) == "SI":
        st.warning(f"⚠️ Ya registraste este código para {dia}.")
        return

    # 6) Marcar ingreso
    db.collection("qrs").document(qr_id).update({field: "SI"})

    # 7) Mostrar bienvenida
    name    = record.get("name", "Usuario")
    empresa = record.get("empresa", "")
    phone   = record.get("phone", "")
    participacion = record.get("tipo_participacion", "")

    st.success(f"✅ ¡{name} ha sido registrado exitosamente!")
    st.write(f"**Empresa:** {empresa}   |   **Teléfono:** {phone}")
    st.markdown(
        f"**¡{name}, bienvenido a SUVECOEX 2025, donde el comercio exterior conecta, crece y se transforma!**"
    )

    # 8) Contador en sesión
    counter_key = "count_dia_1" if dia == "Día 1" else "count_dia_2"
    st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
    st.info(f"👤 Has escaneado {st.session_state[counter_key]} vez(ces) en {dia} hoy.")

    # 9) Bloquear hasta reset
    st.session_state["scan_done"]  = True
    st.session_state["last_qr_id"] = qr_id
