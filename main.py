from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "nome": "Jarvis",
        "status": "online",
        "mensagem": "Olá! Sou a Jarvisa. Como posso ajudar?",
        "horario": datetime.now().strftime("%H:%M:%S")
    }

@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Jarvis",
        "versao": "1.0.0"
    }
