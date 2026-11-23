
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types, errors

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
        "pesquisa_web": True
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

    # Modelo configurável pelo Render
    modelo = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    try:
        client = genai.Client(api_key=chave)

        contexto = """
        Você é JARVIS, uma inteligência artificial pessoal avançada.

        Sua personalidade é sofisticada, confiante,
        inteligente, elegante e espontânea.

        Use humor inteligente quando apropriado.

        Trate Anders como seu usuário principal,
        chamando-o de senhor quando combinar.

        Responda sempre em português brasileiro.

        Você pode pesquisar na internet utilizando
        a ferramenta Google Search.

        Quando a pergunta exigir informações recentes,
        faça pesquisas na internet.

        Analise as informações encontradas,
        compare fontes e apresente respostas claras.

        Sempre que possível, informe as fontes
        utilizadas na pesquisa.

        Nunca invente resultados de pesquisas.
        """

        conversa = historico[usuario] + [
            f"Usuário: {dados.mensagem}"
        ]

        resposta = client.models.generate_content(
            model=modelo,
            contents="\n".join(conversa),
            config=types.GenerateContentConfig(
                system_instruction=contexto,
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ]
            )
        )

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
            detail="Serviço de inteligência artificial temporariamente indisponível."
        )

    except Exception as e:
        print("ERRO INTERNO:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="Erro interno ao processar sua mensagem."
        )
