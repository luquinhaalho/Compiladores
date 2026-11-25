import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.ollama_client import (
    MENSAGEM_IA_INDISPONIVEL,
    MENSAGEM_IA_TIMEOUT,
    explicar,
    montar_pergunta_usuario,
)
from app.mensagens import MENSAGEM_IA_PERGUNTA

client = TestClient(app, raise_server_exceptions=False)


class _RespostaFalsa:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class _ClienteFalso:
    def __init__(self, resposta: _RespostaFalsa | Exception) -> None:
        self._resposta = resposta
        self.ultimo_pedido = None

    def post(self, url: str, json: dict):
        self.ultimo_pedido = {"url": url, "json": json}
        if isinstance(self._resposta, Exception):
            raise self._resposta
        return self._resposta


def test_montar_pergunta_inclui_contexto() -> None:
    texto = montar_pergunta_usuario(
        "AST",
        "Por que a multiplicação está abaixo?",
        "int resultado = 10 + 5 * 2;",
        {"no": {"tipo": "MULTIPLICACAO"}},
    )
    assert "MULTIPLICACAO" in texto
    assert "Por que a multiplicação está abaixo?" in texto
    assert "int resultado = 10 + 5 * 2;" in texto


def test_explicar_sucesso(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    falso = _ClienteFalso(
        _RespostaFalsa(
            200,
            {"message": {"content": "A multiplicação tem precedência maior."}},
        )
    )
    resultado = explicar("AST", "explique", "int x = 1;", {"a": 1}, client=falso)
    assert resultado["sucesso"] is True
    assert "precedência" in resultado["explicacao"]
    assert falso.ultimo_pedido["url"] == "http://ollama:11434/api/chat"
    assert falso.ultimo_pedido["json"]["model"] == "llama3.2"
    assert falso.ultimo_pedido["json"]["stream"] is False
    assert falso.ultimo_pedido["json"]["options"]["num_predict"] == 256
    assert falso.ultimo_pedido["json"]["messages"][0]["role"] == "system"


def test_explicar_timeout(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    falso = _ClienteFalso(httpx.TimeoutException("timeout"))
    resultado = explicar("GERAL", "o que é AST?", "int x = 1;", None, client=falso)
    assert resultado["sucesso"] is False
    assert resultado["mensagem"] == MENSAGEM_IA_TIMEOUT


def test_explicar_indisponivel(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    falso = _ClienteFalso(httpx.ConnectError("offline"))
    resultado = explicar("TOKEN", "explique", "int x = 1;", None, client=falso)
    assert resultado["sucesso"] is False
    assert resultado["mensagem"] == MENSAGEM_IA_INDISPONIVEL


def test_endpoint_exige_pergunta() -> None:
    resposta = client.post(
        "/api/ia/explicar",
        json={"tipo": "GERAL", "pergunta": "  ", "codigo": "int x = 1;"},
    )
    assert resposta.status_code == 400
    assert resposta.json()["mensagem"] == MENSAGEM_IA_PERGUNTA


def test_endpoint_devolve_explicacao(monkeypatch) -> None:
    def falso_explicar(**_kwargs):
        return {
            "sucesso": True,
            "mensagem": "ok",
            "explicacao": "Token IDENTIFICADOR nomeia a variável.",
            "modelo": "llama3.2",
        }

    monkeypatch.setattr("app.main.explicar", falso_explicar)
    resposta = client.post(
        "/api/ia/explicar",
        json={
            "tipo": "TOKEN",
            "pergunta": "Explique o identificador",
            "codigo": "int numero = 10;",
            "contexto": {"token": {"tipo": "IDENTIFICADOR", "lexema": "numero"}},
        },
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["sucesso"] is True
    assert "IDENTIFICADOR" in corpo["explicacao"]
    assert corpo["modelo"] == "llama3.2"


def test_analisar_continua_sem_depender_da_ia() -> None:
    resposta = client.post("/api/analisar", json={"codigo": "int numero = 10;"})
    assert resposta.status_code == 200
    assert resposta.json()["sucesso"] is True
    assert resposta.json()["sintatico"]["sucesso"] is True
