# scan_module.py

import streamlit as st
from firebase_ops import db
import re
import cv2
import numpy as np
from PIL import Image

def escaneo_qr_module():
    """
    Módulo Streamlit para Escanear QR usando OpenCV:
      1) Selección de día (Día 1 / Día 2)
      2) st.camera_input() abre la cámara o uploader
      3) Decodifica el ID del QR con OpenCV
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

    st.markdown("🔍 **Toma una foto del QR o sube una imagen:**")

    # 2) Abrimos la cámara/fallback uploader
    img_file = st.camera_input(
        "📷 Toma foto con QR",
        key="qr_camera"
    )

    # Reinicio si ya escaneaste
    if st.session_state.get("scan_done", False):
        if st.button("🔄 Escanear otro QR"):
            st.session_state["scan_done"] = False
            for k in ("last_qr_id", "count_dia_1", "count_dia_2"):
                st.session_state.pop(k, None)
        return

    # 3) No seguimos hasta tener foto
    if not img_file:
        return

    # 4) Decodificar QR con OpenCV
    image = Image.open(img_file)
    img_array = np.array(image.convert('RGB'))

    detector = cv2.QRCodeDetector()
    data, vertices_array, _ = detector.detectAndDecode(img_array)

    if not data:
        st.error("❌ No se detectó un QR válido en la imagen.")
        return

    # 5) Extraer el ID SUVECO2025-XXXXXX
    m = re.search(r"SUVECO2025-[A-Z2-9]+", data)
    if not m:
        st.error("❌ El contenido no coincide con el formato esperado.")
        return
    qr_id = m.group(0)

    # 6) Validar en Firestore
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

    # 7) Mostrar bienvenida
    name    = record["name"]
    empresa = record["empresa"]
    phone   = record["phone"]

    st.success(f"✅ ¡{name}!")
    st.write(f"**Empresa:** {empresa}   |   **Teléfono:** {phone}")
    st.markdown(
        f"**¡{name}, bienvenido a SUVECOEX 2025, disfruta del summit donde el comercio exterior conecta, crece y se transforma!**"
    )

    # 8) Contador de escaneos en esta sesión
    counter_key = "count_dia_1" if dia == "Día 1" else "count_dia_2"
    st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
    st.info(f"👤 Has escaneado {st.session_state[counter_key]} vez(ces) en {dia} hoy.")

    # 9) Bloquear hasta reinicio
    st.session_state["scan_done"]   = True
    st.session_state["last_qr_id"]  = qr_id