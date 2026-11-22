
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="Xiubala AI",
    description="Assistente pessoal inteligente",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "nome": "Xiubala",
        "status": "online",
        "mensagem": "Olá! Sou a Xiubala. Como posso ajudar?",
        "horario": datetime.now().strftime("%H:%M:%S")
    }

@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Xiubala",
        "versao": "1.0.0"
    }
