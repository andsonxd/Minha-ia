0

import os
import json
import urllib.request
import urllib.error

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="4.0.0"
)


class Mensagem(BaseModel):
    mensagem: str


# Memória temporária
historico = {}


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Jarvis",
        "versao": "4.0.0",
        "motor_principal": "Gemma 4",
        "motor_reserva": None,
        "gemma_configurado": bool(os.getenv("GEMMA_API_URL")),
        "pesquisa_web": True
    }


def contexto_jarvis():
    return """
    Você é JARVIS 4.0, uma inteligência artificial pessoal avançada.

    Sua personalidade é sofisticada, confiante,
    inteligente, elegante e espontânea.

    Use humor inteligente quando apropriado.

    Trate Anders como seu usuário principal,
    chamando-o de senhor quando combinar.

    Responda sempre em português brasileiro.

    Seja preciso, útil e natural.
    Nunca invente informações.
    """


def consultar_gemma(conversa):
    base_url = os.getenv("GEMMA_API_URL", "").rstrip("/")

    if not base_url:
        raise RuntimeError("Gemma não configurado.")

    url = base_url + "/chat/completions"

    mensagens = [
        {
            "role": "system",
            "content": contexto_jarvis()
        }
    ]

    for item in conversa:
        if item.startswith("Usuário: "):
            mensagens.append({
                "role": "user",
                "content": item[9:]
            })
        elif item.startswith("Jarvis: "):
            mensagens.append({
                "role": "assistant",
                "content": item[8:]
            })

    modelo = os.getenv(
        "GEMMA_MODEL",
        "Gemma-4-E2B-it"
    )

    payload = {
        "model": modelo,
        "messages": mensagens,
        "temperature": 0.7
    }

    requisicao = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=90
    ) as resposta:
        resultado = json.loads(
            resposta.read().decode("utf-8")
        )

    texto = resultado["choices"][0]["message"]["content"]

    if not texto:
        raise RuntimeError("Gemma retornou resposta vazia.")

    return texto


@app.post("/chat")
def conversar(dados: Mensagem):

    usuario = "principal"

    if usuario not in historico:
        historico[usuario] = []

    conversa = historico[usuario] + [
        f"Usuário: {dados.mensagem}"
    ]

    resposta_texto = None

    # Motor único: Gemma 4
    try:
        resposta_texto = consultar_gemma(conversa)

    except Exception as e:
        print("ERRO GEMMA:", repr(e))

        raise HTTPException(
            status_code=503,
            detail="O motor Gemma 4 está temporariamente indisponível."
        )

    # Atualiza o histórico somente após resposta válida
    historico[usuario].append(
        f"Usuário: {dados.mensagem}"
    )

    historico[usuario].append(
        f"Jarvis: {resposta_texto}"
    )

    historico[usuario] = historico[usuario][-20:]

    return {
        "assistente": "Jarvis",
        "resposta": resposta_texto,
        "status": "sucesso",
        "motor": "Gemma 4"
    }
