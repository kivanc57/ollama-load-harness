import os
import socket

API_URL = os.environ["API_URL"]
HOST_ID = os.getenv("HOST_ID", socket.gethostname())
MONITORING_SCOPE = os.getenv("MONITORING_SCOPE", "local_ollama")
LLM_MODEL = os.environ["LLM_MODEL"]
USER_AMOUNT = int(os.getenv("USER_AMOUNT", "5"))

