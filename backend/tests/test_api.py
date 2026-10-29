from fastapi.testclient import TestClient

from app.main import app
from app.lexer import analisar_lexico
from app.mensagens import (
    MENSAGEM_BRANCO,
    MENSAGEM_INESPERADA,
    MENSAGEM_REQUISICAO_INVALIDA,
    MENSAGEM_VAZIA,
)

client = TestClient(app, raise_server_exceptions=False)


def test_hello_e_health_continuam_disponiveis() -> None:
    hello = client.get("/api/hello")
    health = client.get("/api/health")

    assert hello.status_code == 200
    assert hello.json() == {"message": "Hello, World!"}
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_codigo_valido_devolve_tokens() -> None:
    codigo = 'int resultado = (10 + 5) * 2; // "ação"'
    resposta = client.post("/api/analisar", json={"codigo": codigo})
    corpo = resposta.json()
    esperado = analisar_lexico(codigo)

    assert resposta.status_code == 200
    assert corpo["recebido"] is True
    assert corpo["sucesso"] is True
    assert corpo["caracteres"] == len(codigo)
    assert corpo["erros"] == []
    assert [(item["tipo"], item["lexema"]) for item in corpo["tokens"]] == [
        (token.tipo, token.lexema) for token in esperado.tokens
    ]
    assert "Análise léxica concluída" in corpo["mensagem"]
    assert "Traceback" not in resposta.text
    assert "site-packages" not in resposta.text


def test_erro_lexico_nao_interrompe_e_usa_http_200() -> None:
    resposta = client.post("/api/analisar", json={"codigo": "int a = 1 @ 2;"})
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["recebido"] is True
    assert corpo["sucesso"] is False
    assert any(token["lexema"] == "int" for token in corpo["tokens"])
    assert corpo["erros"][0]["tipo"] == "ERRO_LEXICO"
    assert corpo["erros"][0]["lexema"] == "@"
    assert "linha 1, coluna" in corpo["erros"][0]["mensagem"]
    assert "Traceback" not in resposta.text


def test_entrada_vazia() -> None:
    resposta = client.post("/api/analisar", json={"codigo": ""})

    assert resposta.status_code == 400
    assert resposta.json() == {"recebido": False, "mensagem": MENSAGEM_VAZIA}


def test_entrada_so_com_espacos() -> None:
    resposta = client.post("/api/analisar", json={"codigo": " \n\t "})

    assert resposta.status_code == 400
    assert resposta.json() == {"recebido": False, "mensagem": MENSAGEM_BRANCO}


def test_campo_obrigatorio_ausente() -> None:
    resposta = client.post("/api/analisar", json={})

    assert resposta.status_code == 400
    assert resposta.json() == {
        "recebido": False,
        "mensagem": MENSAGEM_REQUISICAO_INVALIDA,
    }


def test_codigo_com_tipo_invalido() -> None:
    resposta = client.post("/api/analisar", json={"codigo": 10})

    assert resposta.status_code == 400
    assert resposta.json()["mensagem"] == MENSAGEM_REQUISICAO_INVALIDA
    assert "loc" not in resposta.text


def test_corpo_que_nao_e_json() -> None:
    resposta = client.post(
        "/api/analisar",
        content=b"int numero = 10;",
        headers={"Content-Type": "text/plain"},
    )

    assert resposta.status_code == 400
    assert resposta.json()["mensagem"] == MENSAGEM_REQUISICAO_INVALIDA
    assert "Traceback" not in resposta.text


def test_erro_interno_nao_expoe_detalhe(monkeypatch) -> None:
    def falha(_codigo: str) -> str:
        raise RuntimeError("senha=segredo caminho=/srv/app")

    monkeypatch.setattr("app.main.classificar_codigo", falha)
    resposta = client.post("/api/analisar", json={"codigo": "int numero = 10;"})

    assert resposta.status_code == 500
    corpo = resposta.json()
    assert corpo == {"recebido": False, "mensagem": MENSAGEM_INESPERADA}
    assert "segredo" not in resposta.text
    assert "RuntimeError" not in resposta.text
    assert "/srv/app" not in resposta.text


def test_falha_do_scanner_nao_expoe_detalhe(monkeypatch) -> None:
    def falha(_codigo: str):
        raise RuntimeError("senha=segredo caminho=/srv/lexer")

    monkeypatch.setattr("app.main.analisar_lexico", falha)
    resposta = client.post("/api/analisar", json={"codigo": "int numero = 10;"})

    assert resposta.status_code == 500
    assert resposta.json() == {"recebido": False, "mensagem": MENSAGEM_INESPERADA}
    assert "segredo" not in resposta.text
    assert "RuntimeError" not in resposta.text


def test_rota_desconhecida_nao_vaza_rastreamento() -> None:
    resposta = client.get("/api/nao-existe")

    assert resposta.status_code == 404
    assert MENSAGEM_INESPERADA not in resposta.text
    assert "Traceback" not in resposta.text
