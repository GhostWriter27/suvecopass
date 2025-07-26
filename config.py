# config.py

import streamlit as st

# Carga la sección [firebase] de tus secrets.toml
firebase_config = st.secrets["firebase"]

# Ya no mostramos el contenido de firebase_config en pantalla
# (❌) st.write("🔑 DEBUG → firebase_config:", firebase_config)