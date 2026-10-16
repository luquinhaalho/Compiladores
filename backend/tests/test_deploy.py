"""Sobe o Compose e confirma o contrato através do Nginx.

Não faz parte da suíte padrão: a construção das imagens é lenta e exige o
daemon. Rode com ``pytest -m deploy --override-ini="addopts="``.
"""

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def _docker_disponivel() -> bool:
    return shutil.which("docker") is not None


@pytest.mark.deploy
def test_compose_entrega_hello_e_analise() -> None:
    if not _docker_disponivel():
        pytest.skip("Docker não está instalado neste ambiente")

    subir = subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd=RAIZ,
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if subir.returncode != 0:
        pytest.fail(subir.stderr or subir.stdout)

    try:
        _esperar_http("http://127.0.0.1:3000/api/health")
        hello = json.loads(_ler("http://127.0.0.1:3000/api/hello"))
        assert hello == {"message": "Hello, World!"}

        codigo = "int numero = 10;"
        pedido = urllib.request.Request(
            "http://127.0.0.1:3000/api/analisar",
            data=json.dumps({"codigo": codigo}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            corpo = json.load(resposta)
            assert resposta.status == 200
        assert corpo["recebido"] is True
        assert corpo["caracteres"] == len(codigo)

        vazio = urllib.request.Request(
            "http://127.0.0.1:3000/api/analisar",
            data=json.dumps({"codigo": "   "}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as erro:
            urllib.request.urlopen(vazio, timeout=10)
        assert erro.value.code == 400
    finally:
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=RAIZ,
            check=False,
            timeout=120,
        )


def _esperar_http(url: str) -> None:
    ultimo_erro = "sem resposta"
    for _ in range(40):
        try:
            _ler(url)
            return
        except Exception as exc:  # noqa: BLE001 — a sondagem só registra a última falha
            ultimo_erro = str(exc)
            time.sleep(1)
    pytest.fail(f"o frontend não ficou disponível: {ultimo_erro}")


def _ler(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as resposta:
        return resposta.read().decode("utf-8")
