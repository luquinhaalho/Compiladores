"""API do laboratório de compiladores.

Fluxo da Etapa 4: validar entrada → scanner → se não houver erros léxicos,
parser → AST. Os campos da Etapa 3 (sucesso, tokens, erros) continuam
representando o resultado léxico. A rota ``GET /api/hello`` permanece.
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
from app.mensagens import (
    MENSAGEM_IA_PERGUNTA,
    MENSAGEM_INESPERADA,
    MENSAGEM_REQUISICAO_INVALIDA,
)
from app.ollama_client import explicar
from app.parser import ResultadoSintatico, analisar_sintatico, mensagem_sintatica
from app.validacao import classificar_codigo, mensagem_para

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Compiladores — API",
    description="Laboratório educacional de AST para um subconjunto didático de Java.",
    version="0.4.1",
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


class ErroLexicoResposta(BaseModel):
    tipo: str
    lexema: str
    linha: int
    coluna: int
    mensagem: str


class ErroSintaticoResposta(BaseModel):
    tipo: str
    linha: int
    coluna: int
    encontrado: str
    esperado: list[str]
    mensagem: str
    regra: str | None = None


class LexicoResposta(BaseModel):
    sucesso: bool
    tokens: list[TokenResposta]
    erros: list[ErroLexicoResposta]


class SintaticoResposta(BaseModel):
    executado: bool
    sucesso: bool | None = None
    ast: dict | None = None
    erros: list[ErroSintaticoResposta] = []


class RespostaAnalise(BaseModel):
    recebido: bool
    mensagem: str
    caracteres: int | None = None
    # Campos da Etapa 3: resultado léxico.
    sucesso: bool | None = None
    tokens: list[TokenResposta] | None = None
    erros: list[ErroLexicoResposta] | None = None
    lexico: LexicoResposta | None = None
    sintatico: SintaticoResposta | None = None


class PedidoExplicacao(BaseModel):
    tipo: str = Field(min_length=1)
    pergunta: str = Field(min_length=0)
    codigo: str = ""
    contexto: dict | None = None


class RespostaExplicacao(BaseModel):
    sucesso: bool
    mensagem: str
    explicacao: str | None = None
    modelo: str | None = None


@app.exception_handler(RequestValidationError)
async def requisicao_invalida(request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "recebido": False,
            "mensagem": MENSAGEM_REQUISICAO_INVALIDA,
        },
    )


@app.exception_handler(Exception)
async def erro_inesperado(request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("falha ao processar a requisição")
    return JSONResponse(
        status_code=500,
        content={"recebido": False, "mensagem": MENSAGEM_INESPERADA},
    )


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello, World!"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _token_resposta(token: Token) -> TokenResposta:
    return TokenResposta(
        tipo=token.tipo,
        lexema=token.lexema,
        linha=token.linha,
        coluna=token.coluna,
    )


def _mensagem_combinada(lexico_msg: str, sintatico: ResultadoSintatico) -> str:
    return lexico_msg + " " + mensagem_sintatica(sintatico)


@app.post("/api/analisar", response_model=RespostaAnalise)
def analisar(pedido: PedidoAnalise) -> RespostaAnalise:
    """Valida, tokeniza e, se o léxico estiver limpo, analisa a sintaxe."""
    situacao = classificar_codigo(pedido.codigo)
    if situacao != "aceito":
        return JSONResponse(
            status_code=400,
            content={"recebido": False, "mensagem": mensagem_para(situacao)},
        )

    lexico = analisar_lexico(pedido.codigo)
    tokens = [_token_resposta(token) for token in lexico.tokens]
    erros_lexicos = [
        ErroLexicoResposta(
            tipo=erro.tipo,
            lexema=erro.lexema,
            linha=erro.linha,
            coluna=erro.coluna,
            mensagem=erro.mensagem,
        )
        for erro in lexico.erros
    ]
    lexico_resposta = LexicoResposta(
        sucesso=lexico.sucesso,
        tokens=tokens,
        erros=erros_lexicos,
    )

    if not lexico.sucesso:
        sintatico = ResultadoSintatico(
            sucesso=False, ast=None, erros=[], executado=False
        )
        sintatico_resposta = SintaticoResposta(
            executado=False, sucesso=None, ast=None, erros=[]
        )
    else:
        sintatico = analisar_sintatico(lexico.tokens)
        sintatico_resposta = SintaticoResposta(
            executado=True,
            sucesso=sintatico.sucesso,
            ast=sintatico.ast.para_dict() if sintatico.ast else None,
            erros=[
                ErroSintaticoResposta(
                    tipo=erro.tipo,
                    linha=erro.linha,
                    coluna=erro.coluna,
                    encontrado=erro.encontrado,
                    esperado=erro.esperado,
                    mensagem=erro.mensagem,
                    regra=erro.regra,
                )
                for erro in sintatico.erros
            ],
        )

    return RespostaAnalise(
        recebido=True,
        sucesso=lexico.sucesso,
        mensagem=_mensagem_combinada(mensagem_analise(lexico), sintatico),
        caracteres=len(pedido.codigo),
        tokens=tokens,
        erros=erros_lexicos,
        lexico=lexico_resposta,
        sintatico=sintatico_resposta,
    )


@app.post("/api/ia/explicar", response_model=RespostaExplicacao)
def ia_explicar(pedido: PedidoExplicacao) -> RespostaExplicacao:
    """Pede uma explicação didática ao Ollama sem alterar o compilador."""
    pergunta = pedido.pergunta.strip()
    if not pergunta:
        return JSONResponse(
            status_code=400,
            content={
                "sucesso": False,
                "mensagem": MENSAGEM_IA_PERGUNTA,
                "explicacao": None,
                "modelo": None,
            },
        )
    resultado = explicar(
        tipo=pedido.tipo.strip() or "GERAL",
        pergunta=pergunta,
        codigo=pedido.codigo,
        contexto=pedido.contexto,
    )
    return RespostaExplicacao(**resultado)
