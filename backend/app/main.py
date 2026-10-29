"""API do laboratório de compiladores.

A entrada continua sendo validada como na segunda etapa. Quando o texto tem
conteúdo, o scanner produz tokens e erros léxicos. A análise sintática e a
semântica ficam para as etapas seguintes. A rota ``GET /api/hello`` permanece
como prova de vida da primeira etapa.
"""

import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.lexer import Token, analisar_lexico, mensagem_analise
from app.mensagens import MENSAGEM_INESPERADA, MENSAGEM_REQUISICAO_INVALIDA
from app.validacao import classificar_codigo, mensagem_para

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Compiladores — API",
    description="Laboratório educacional de AST para um subconjunto didático de Java.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class PedidoAnalise(BaseModel):
    codigo: str = Field(min_length=0)


class TokenResposta(BaseModel):
    tipo: str
    lexema: str
    linha: int
    coluna: int


class ErroResposta(BaseModel):
    tipo: str
    lexema: str
    linha: int
    coluna: int
    mensagem: str


class RespostaAnalise(BaseModel):
    recebido: bool
    mensagem: str
    caracteres: int | None = None
    sucesso: bool | None = None
    tokens: list[TokenResposta] | None = None
    erros: list[ErroResposta] | None = None


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


def _token_resposta(token: Token) -> TokenResposta:
    return TokenResposta(
        tipo=token.tipo,
        lexema=token.lexema,
        linha=token.linha,
        coluna=token.coluna,
    )


@app.post("/api/analisar", response_model=RespostaAnalise)
def analisar(pedido: PedidoAnalise) -> RespostaAnalise:
    """Valida o texto e, se houver conteúdo, executa o scanner."""
    situacao = classificar_codigo(pedido.codigo)
    if situacao != "aceito":
        return JSONResponse(
            status_code=400,
            content={"recebido": False, "mensagem": mensagem_para(situacao)},
        )
    resultado = analisar_lexico(pedido.codigo)
    return RespostaAnalise(
        recebido=True,
        sucesso=resultado.sucesso,
        mensagem=mensagem_analise(resultado),
        caracteres=len(pedido.codigo),
        tokens=[_token_resposta(token) for token in resultado.tokens],
        erros=[
            ErroResposta(
                tipo=erro.tipo,
                lexema=erro.lexema,
                linha=erro.linha,
                coluna=erro.coluna,
                mensagem=erro.mensagem,
            )
            for erro in resultado.erros
        ],
    )
