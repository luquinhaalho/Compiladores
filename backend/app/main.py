"""Ponto de entrada da API da primeira etapa.

Nesta etapa a API apenas confirma que o frontend consegue alcançá-la.
As etapas seguintes vão acrescentar análise léxica, sintática e a AST.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Compiladores — API",
    description="Laboratório educacional de AST para um subconjunto didático de Java.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello() -> dict[str, str]:
    """Rota de prova de vida usada pelo frontend na primeira etapa."""
    return {"message": "Hello, World!"}


@app.get("/api/health")
def health() -> dict[str, str]:
    """Usada pelo healthcheck do contêiner."""
    return {"status": "ok"}
