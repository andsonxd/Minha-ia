
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI, APIError

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="2.0.0"
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
        "versao": "2.0.0"
    }

@app.post("/chat")
def conversar(dados: Mensagem):

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Chave da OpenAI não configurada."
        )

    try:
        client = OpenAI()

        resposta = client.responses.create(
            model="gpt-4o-mini",
            instructions=(
                "Você é JARVIS, um assistente pessoal inteligente. "
                "Responda em português brasileiro, de forma "
                "educada, clara e prestativa."
            ),
            input=dados.mensagem
        )

        return {
            "assistente": "Jarvis",
            "resposta": resposta.output_text,
            "status": "sucesso"
        }

    except APIError:
        raise HTTPException(
            status_code=502,
            detail="Erro ao consultar a inteligência artificial."
        )
