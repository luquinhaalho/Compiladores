"""API do laboratório de compiladores.

A segunda etapa recebe o código-fonte, valida a entrada e devolve uma
resposta estruturada. A análise léxica, sintática e semântica fica para
as etapas seguintes. A rota ``GET /api/hello`` permanece como prova de vida
da primeira etapa.
"""

import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.mensagens import MENSAGEM_INESPERADA, MENSAGEM_REQUISICAO_INVALIDA
from app.validacao import classificar_codigo, mensagem_para

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Compiladores — API",
    description="Laboratório educacional de AST para um subconjunto didático de Java.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class PedidoAnalise(BaseModel):
    codigo: str = Field(min_length=0)


class RespostaAnalise(BaseModel):
    recebido: bool
    mensagem: str
    caracteres: int | None = None


@app.exception_handler(RequestValidationError)
async def requisicao_invalida(request, exc: RequestValidationError) -> JSONResponse:
    """Converte o erro padrão do FastAPI em uma mensagem compreensível."""
    return JSONResponse(
        status_code=400,
        content={
            "recebido": False,
            "mensagem": MENSAGEM_REQUISICAO_INVALIDA,
        },
    )


@app.exception_handler(Exception)
async def erro_inesperado(request, exc: Exception):
    """Evita devolver rastreamento interno ao cliente.

    ``HTTPException`` continua no tratamento padrão do framework, para que
    uma rota inexistente siga respondendo 404.
    """
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("falha ao processar a requisição")
    return JSONResponse(
        status_code=500,
        content={"recebido": False, "mensagem": MENSAGEM_INESPERADA},
    )


@app.get("/api/hello")
def hello() -> dict[str, str]:
    """Prova de vida da primeira etapa."""
    return {"message": "Hello, World!"}


@app.get("/api/health")
def health() -> dict[str, str]:
    """Usada pelo healthcheck do contêiner."""
    return {"status": "ok"}


@app.post("/api/analisar", response_model=RespostaAnalise)
def analisar(pedido: PedidoAnalise) -> RespostaAnalise:
    """Recebe o programa-fonte e aplica só a validação inicial."""
    situacao = classificar_codigo(pedido.codigo)
    if situacao != "aceito":
        return JSONResponse(
            status_code=400,
            content={"recebido": False, "mensagem": mensagem_para(situacao)},
        )
    return RespostaAnalise(
        recebido=True,
        mensagem=mensagem_para(situacao),
        caracteres=len(pedido.codigo),
    )
