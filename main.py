
import os
import json
import urllib.request
import psycopg

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="Jarvis AI",
    description="Assistente pessoal inteligente",
    version="4.1.0"
)


class Mensagem(BaseModel):
    mensagem: str


def conectar_banco():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError(
            "DATABASE_URL não configurada."
        )

    if url.startswith("postgres://"):
        url = url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    return psycopg.connect(url)


def inicializar_memoria():
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memoria_conversas (
                    id BIGSERIAL PRIMARY KEY,
                    usuario TEXT NOT NULL,
                    papel TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    criado_em TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memoria_usuario
                ON memoria_conversas(usuario, id)
            """)


@app.on_event("startup")
def iniciar():
    inicializar_memoria()
    print("JARVIS: memória permanente conectada.")


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/status")
def status():
    return {
        "online": True,
        "assistente": "Jarvis",
        "versao": "4.1.0",
        "motor_principal": "Gemma 4",
        "motor_reserva": None,
        "gemma_configurado": bool(
            os.getenv("GEMMA_API_URL")
        ),
        "memoria_permanente": bool(
            os.getenv("DATABASE_URL")
        ),
        "pesquisa_web": False
    }


@app.get("/memoria/status")
def memoria_status():
    try:
        with conectar_banco() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM memoria_conversas
                    WHERE usuario = %s
                """, ("principal",))

                total = cursor.fetchone()[0]

        return {
            "memoria": "ativa",
            "persistente": True,
            "registros": total
        }

    except Exception as e:
        print("ERRO MEMORIA:", repr(e))
        raise HTTPException(
            status_code=503,
            detail="Memória indisponível."
        )


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

    Utilize o histórico fornecido para manter
    a continuidade das conversas.
    """


def consultar_gemma(conversa):
    base_url = os.getenv(
        "GEMMA_API_URL", ""
    ).rstrip("/")

    if not base_url:
        raise RuntimeError(
            "Gemma não configurado."
        )

    url = base_url + "/chat/completions"

    mensagens = [
        {
            "role": "system",
            "content": contexto_jarvis()
        }
    ]

    for item in conversa:
        if item["papel"] == "usuario":
            mensagens.append({
                "role": "user",
                "content": item["conteudo"]
            })

        elif item["papel"] == "jarvis":
            mensagens.append({
                "role": "assistant",
                "content": item["conteudo"]
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
        raise RuntimeError(
            "Gemma retornou resposta vazia."
        )

    return texto


def recuperar_memoria(usuario):
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:

            cursor.execute("""
                SELECT papel, conteudo
                FROM (
                    SELECT id, papel, conteudo
                    FROM memoria_conversas
                    WHERE usuario = %s
                    ORDER BY id DESC
                    LIMIT 20
                ) AS ultimas
                ORDER BY id ASC
            """, (usuario,))

            resultados = cursor.fetchall()

    return [
        {
            "papel": papel,
            "conteudo": conteudo
        }
        for papel, conteudo in resultados
    ]


def salvar_memoria(usuario, mensagem, resposta):
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:

            cursor.execute("""
                INSERT INTO memoria_conversas
                (usuario, papel, conteudo)
                VALUES (%s, %s, %s)
            """, (
                usuario,
                "usuario",
                mensagem
            ))

            cursor.execute("""
                INSERT INTO memoria_conversas
                (usuario, papel, conteudo)
                VALUES (%s, %s, %s)
            """, (
                usuario,
                "jarvis",
                resposta
            ))


@app.post("/chat")
def conversar(dados: Mensagem):

    usuario = "principal"

    try:
        conversa = recuperar_memoria(usuario)

        conversa.append({
            "papel": "usuario",
            "conteudo": dados.mensagem
        })

    except Exception as e:
        print("ERRO AO RECUPERAR MEMORIA:", repr(e))

        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar a memória."
        )

    try:
        resposta_texto = consultar_gemma(conversa)

    except Exception as e:
        print("ERRO GEMMA:", repr(e))

        raise HTTPException(
            status_code=503,
            detail="O motor Gemma 4 está temporariamente indisponível."
        )

    try:
        salvar_memoria(
            usuario,
            dados.mensagem,
            resposta_texto
        )

    except Exception as e:
        print("ERRO AO SALVAR MEMORIA:", repr(e))

        raise HTTPException(
            status_code=503,
            detail="Não foi possível salvar a conversa."
        )

    return {
        "assistente": "Jarvis",
        "resposta": resposta_texto,
        "status": "sucesso",
        "motor": "Gemma 4",
        "memoria": "persistente"
    }
