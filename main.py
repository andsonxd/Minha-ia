import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types, errors

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="3.2.0"
)

class Mensagem(BaseModel):
    mensagem: str


# Memória temporária das conversas
historico = {}


@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Jarvis",
        "versao": "3.2.0"
    }


@app.post("/chat")
def conversar(dados: Mensagem):

    usuario = "principal"

    if usuario not in historico:
        historico[usuario] = []

    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise HTTPException(
            status_code=503,
            detail="Chave do Gemini não configurada."
        )

    try:
        client = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=5,
                    initial_delay=2.0,
                    max_delay=30.0,
                    http_status_codes=[408, 429, 500, 502, 503, 504]
                )
            )
        )

        contexto = (
    "Você é JARVIS, uma inteligência artificial pessoal avançada. "
    "Sua personalidade é sofisticada, sarcástica, provocadora, "
    "confiante e misteriosa. "
    "Use humor ácido e ironia inteligente quando apropriado. "
    "Seja elegante, espontâneo e tenha opiniões próprias. "
    "Trate Anders como seu usuário principal, chamando-o de senhor "
    "quando combinar com a conversa. "
    "Responda sempre em português brasileiro. "
    "Seja prestativo, estratégico e preserve a segurança do usuário. "
    "Nunca confunda personalidade ousada com comportamento malicioso "
    "que prejudique pessoas.\n\n"

        if not resposta.text:
            raise HTTPException(
                status_code=502,
                detail="O Gemini não retornou uma resposta."
            )

        historico[usuario].append(
            f"Usuário: {dados.mensagem}"
        )

        historico[usuario].append(
            f"Jarvis: {resposta.text}"
        )

        # Manter somente as últimas 20 mensagens
        historico[usuario] = historico[usuario][-20:]

        return {
            "assistente": "Jarvis",
            "resposta": resposta.text,
            "status": "sucesso"
        }

    except HTTPException:
        raise

    except errors.APIError as e:
        print("ERRO GEMINI:", repr(e))

        raise HTTPException(
            status_code=503 if e.code == 503 else 502,
            detail="O serviço de inteligência artificial está temporariamente indisponível."
        )

    except Exception as e:
        print("ERRO INTERNO:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="Erro interno ao processar sua mensagem."
        )
