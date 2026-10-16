from fastapi.testclient import TestClient

from app.main import app
from app.mensagens import (
    MENSAGEM_BRANCO,
    MENSAGEM_INESPERADA,
    MENSAGEM_RECEBIDO,
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


def test_codigo_valido_e_recebido() -> None:
    codigo = 'int resultado = (10 + 5) * 2; // "ação"'
    resposta = client.post("/api/analisar", json={"codigo": codigo})
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["recebido"] is True
    assert corpo["mensagem"] == MENSAGEM_RECEBIDO
    assert corpo["caracteres"] == len(codigo)
    assert "Traceback" not in resposta.text
    assert "site-packages" not in resposta.text


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


def test_rota_desconhecida_nao_vaza_rastreamento() -> None:
    resposta = client.get("/api/nao-existe")

    assert resposta.status_code == 404
    assert MENSAGEM_INESPERADA not in resposta.text
    assert "Traceback" not in resposta.text
