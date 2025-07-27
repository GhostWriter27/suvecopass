# manual_search_module.py

import streamlit as st
import requests
from firebase_ops import db
from qr_module import enviar_por_email_silencioso

def busqueda_manual_module():
    st.header("🔍 Búsqueda manual de QR por correo")

    # --- ESTILOS ---
    st.markdown("""
    <style>
    /* Input */
    input {
        background-color: #fff !important;
        color: #000 !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
    }

    /* Card container */
    .result-card {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .result-card img {
        flex: 0 0 120px;
        width: 120px;
        height: 120px;
        object-fit: cover;
        border-radius: 8px;
        margin-right: 1rem;
    }
    .result-details {
        flex: 1;
        min-width: 0;
    }
    .result-details p {
        margin: 0.3rem 0;
    }
    .label {
        font-weight: bold;
        color: #333;
    }
    .value {
        color: #222;
    }

    /* Botón grande */
    .stButton > button {
        width: 100% !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- BÚSQUEDA ---
    email = st.text_input("Ingresa el correo electrónico del cliente:", key="search_email")

    if st.button("🔍 Buscar", key="btn_buscar"):
        if not email:
            st.warning("Por favor, escribe un correo.")
        else:
            query = db.collection("qrs").where("email", "==", email).get()
            if not query:
                st.error("❌ No se encontró ningún registro con ese correo.")
            else:
                # Document encontrado
                doc = query[0].to_dict()
                st.success("✅ Registro encontrado")

                # Guardamos en sesión los datos y el payload
                st.session_state["last_search_doc"] = doc
                st.session_state["last_search_payload"] = {
                    "name":               doc.get("name", ""),
                    "email":              doc.get("email", ""),
                    "phone":              doc.get("phone", ""),
                    "empresa":            doc.get("empresa", ""),
                    "cargo":              doc.get("cargo", ""),
                    "nicho":              doc.get("nicho", ""),
                    "tipo_participacion": doc.get("tipo_participacion", ""),
                    "codigo_entrada":     doc.get("codigo_entrada", "")
                }

    # --- MUESTRA TARJETA + BOTÓN DE REENVÍO SI HAY PAYLOAD EN SESIÓN ---
    if st.session_state.get("last_search_payload"):
        doc = st.session_state["last_search_doc"]

        # Mostramos la tarjeta y el botón en una fila de 3 columnas
        cols = st.columns([2, 1, 2], gap="large")
        with cols[0]:
            st.markdown(f"""
            <div class="result-card">
                <img src="{doc.get('codigo_entrada','')}" alt="Código QR" />
                <div class="result-details">
                    <p><span class="label">Nombre:</span> <span class="value">{doc.get('name','')}</span></p>
                    <p><span class="label">Empresa:</span> <span class="value">{doc.get('empresa','')}</span></p>
                    <p><span class="label">Tipo de participación:</span> <span class="value">{doc.get('tipo_participacion','')}</span></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            # Centramos el botón en su celda
            st.write("")  # espaciador superior
            if st.button("✉️ Reenviar QR por email", key="btn_reenviar"):
                ok = enviar_por_email_silencioso(st.session_state["last_search_payload"])
                if ok:
                    st.success("📧 Enviado correctamente.")
                else:
                    st.error("❌ Falló el envío. Intenta de nuevo.")
            st.write("")  # espaciador inferior