import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="3.0.0"
)

class Mensagem(BaseModel):
    mensagem: str

@app.get("/")
def read_root():
    return {
        "nome": "Jarvis",
        "status": "online",
        "mensagem": "Olá! Sou o Jarvis. Como posso ajudar?",
        "horario": datetime.now().strftime("%H:%M:%S")
    }

@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Jarvis",
        "versao": "3.0.0"
    }

@app.post("/chat")
def conversar(dados: Mensagem):

    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise HTTPException(
            status_code=503,
            detail="Chave do Gemini não configurada."
        )

    try:
        client = genai.Client(api_key=chave)

        resposta = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=(
                "Você é JARVIS, um assistente pessoal inteligente. "
                "Responda em português brasileiro, de forma educada, "
                "clara e prestativa.\n\n"
                f"Usuário: {dados.mensagem}"
            )
        )

        return {
            "assistente": "Jarvis",
            "resposta": resposta.text,
            "status": "sucesso"
        }

    except Exception as e:
        print("ERRO REAL DO GEMINI:", repr(e))

        raise HTTPException(
            status_code=502,
            detail=f"Erro Gemini: {type(e).__name__}"
        )
