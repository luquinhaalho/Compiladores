"""Garante que a interface oferece os três exemplos do subconjunto."""

import json
from pathlib import Path

EXEMPLOS = (
    Path(__file__).resolve().parents[2] / "frontend" / "public" / "examples.json"
)


def test_tres_exemplos_com_codigo_util() -> None:
    lista = json.loads(EXEMPLOS.read_text(encoding="utf-8"))

    assert len(lista) >= 3
    identificadores = [item["id"] for item in lista]
    assert len(identificadores) == len(set(identificadores))

    for item in lista:
        assert item["titulo"].strip()
        assert item["demonstra"].strip()
        assert item["codigo"].strip()
        assert item["codigo"].endswith("\n")
