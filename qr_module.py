import streamlit as st
import qrcode
import io
import random
import string
import pandas as pd
import requests
from firebase_ops import bucket, check_email_exists, save_qr_record, get_all_qr_records

# URL del webhook de HighLevel
WEBHOOK_URL = (
    "https://services.leadconnectorhq.com/hooks/"
    "w49RPC45xtJKaOD14kiR/webhook-trigger/"
    "028e39c5-7319-446e-a93b-58e1252513f6"
)

# Caracteres permitidos para el sufijo del ID
ID_CHARS = ''.join(c for c in (string.ascii_uppercase + string.digits) if c not in "IO01")


def enviar_por_email_silencioso(payload: dict) -> bool:
    """
    Dispara el webhook POST sin mostrar nada al usuario.
    Devuelve True si fue 200-299, False en otro caso.
    """
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return r.ok
    except:
        return False


def generar_codigo_qr_module():
    st.header("📤 Generación de Código QR")

    with st.container():
        st.subheader("📝 Datos del Participante")

        with st.form("qr_form"):
            col1, col2 = st.columns(2)
            with col1:
                name  = st.text_input("Nombre completo", key="qr_name")
                email = st.text_input("Correo electrónico", key="qr_email")
                phone = st.text_input("Teléfono", key="qr_phone")
                cargo = st.text_input("Cargo", key="qr_cargo")
            with col2:
                empresa = st.text_input("Empresa", key="qr_empresa")
                nicho   = st.text_input("Nicho", key="qr_nicho")
                tipo_participacion = st.selectbox(
                    "Tipo de participación",
                    [
                        "Entrada General", "Entrada Online", "Entrada Premium",
                        "Entrada Cortesía Premium", "Entrada Patrocinio Premium",
                        "Patrocinio Conexión", "Patrocinio Conocimiento", "Patrocinio Cumbre",
                        "Patrocinio RespaldarES", "Patrocinio Lanyards", "Patrocinio Bolsas",
                        "Patrocinio Libretas", "Patrocinio Marco Digital"
                    ],
                    key="qr_tipo"
                )

            submitted = st.form_submit_button("✅ Generar QR")

    qr_id  = None
    qr_url = None

    if submitted:
        if not (name and email and phone):
            st.error("❗ Debes completar nombre, email y teléfono.")
        elif check_email_exists(email):
            st.error("❗ Ya existe un registro con ese correo.")
        else:
            # Generar ID único
            suffix = ''.join(random.choices(ID_CHARS, k=10))
            qr_id  = f"SUVECO2025-{suffix}"

            # Crear QR
            qr_data = f"https://suvecopass.app/scan/{qr_id}"
            qr_img  = qrcode.make(qr_data)

            # Subir a Storage
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            buffer.seek(0)
            blob = bucket.blob(f"qrs/{qr_id}.png")
            blob.upload_from_string(buffer.read(), content_type="image/png")
            blob.make_public()
            qr_url = blob.public_url

            # Guardar en Firestore
            record = {
                "name": name,
                "email": email,
                "phone": phone,
                "empresa": empresa,
                "cargo": cargo,
                "nicho": nicho,
                "tipo_participacion": tipo_participacion,
                "id_qr": qr_id,
                "codigo_entrada": qr_url,
                "escaneado_dia_1": "NO",
                "escaneado_dia_2": "NO"
            }
            save_qr_record(record)  # ✅ Corregido: solo se pasa 1 argumento

            # Guardamos en session para el envío posterior
            st.session_state["last_payload"] = {
                "name": name,
                "email": email,
                "phone": phone,
                "empresa": empresa,
                "cargo": cargo,
                "nicho": nicho,
                "tipo_participacion": tipo_participacion,
                "codigo_entrada": qr_url
            }

            st.success("✅ QR generado correctamente.")
            st.image(qr_url, caption=f"QR: {qr_id}", use_column_width=True)

    # Botón "Enviar por email"
    if "last_payload" in st.session_state:
        if st.button("✉️ Enviar por email"):
            ok = enviar_por_email_silencioso(st.session_state["last_payload"])
            if ok:
                st.success("📧 Enviado correctamente.")
            else:
                st.error("❌ Falló el envío. Intenta de nuevo.")

    # Botón para exportar histórico
    with st.container():
        st.markdown("---")
        if st.button("📥 Descargar registros históricos"):
            docs = get_all_qr_records()
            df   = pd.DataFrame(docs)

            columnas = [
                "id_qr", "name", "email", "phone", "empresa", "cargo",
                "nicho", "tipo_participacion", "codigo_entrada",
                "escaneado_dia_1", "escaneado_dia_2"
            ]
            df = df[[c for c in columnas if c in df.columns]]

            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            st.download_button(
                "📥 Descargar Excel con todos los registros",
                buf.getvalue(),
                "registros_qrs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )