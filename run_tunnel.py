# run_tunnel.py

import os
import subprocess

# 1) Fuerza la carpeta TMP/TEMP a un directorio 'ngrok_tmp' en tu proyecto
project_tmp = os.path.join(os.getcwd(), "ngrok_tmp")
os.makedirs(project_tmp, exist_ok=True)
os.environ["TMP"] = project_tmp
os.environ["TEMP"] = project_tmp

# 2) Importa pyngrok después de cambiar TMP/TEMP
from pyngrok import ngrok, conf

# (Opcional) Si ya descargaste manualmente ngrok.exe en la raíz del proyecto:
# conf.get_default().ngrok_path = os.path.join(os.getcwd(), "ngrok.exe")

# 3) Abre el túnel HTTPS en el puerto donde corre tu Streamlit (8501)
public_url = ngrok.connect(8501, bind_tls=True)
print(f"🔥 Tunnel URL: {public_url}")

# 4) Ajusta variables de entorno para Streamlit
os.environ["STREAMLIT_SERVER_PORT"]         = "8501"
os.environ["STREAMLIT_SERVER_ADDRESS"]      = "0.0.0.0"
os.environ["STREAMLIT_SERVER_ENABLECORS"]   = "false"

# 5) Lanza tu app de Streamlit
subprocess.run(["streamlit", "run", "app.py"])