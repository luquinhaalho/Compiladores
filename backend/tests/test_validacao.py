import pytest

from app.mensagens import MENSAGEM_BRANCO, MENSAGEM_RECEBIDO, MENSAGEM_VAZIA
from app.validacao import classificar_codigo, mensagem_para


@pytest.mark.parametrize(
    ("codigo", "situacao"),
    [
        ("", "vazio"),
        (" ", "branco"),
        ("\n\t  ", "branco"),
        ("int numero = 10;", "aceito"),
        ("  int numero = 10;  ", "aceito"),
        ('int nome = 1; // "ação" <>&', "aceito"),
    ],
)
def test_classifica_entradas(codigo: str, situacao: str) -> None:
    assert classificar_codigo(codigo) == situacao


def test_mensagens_de_cada_situacao() -> None:
    assert mensagem_para("vazio") == MENSAGEM_VAZIA
    assert mensagem_para("branco") == MENSAGEM_BRANCO
    assert mensagem_para("aceito") == MENSAGEM_RECEBIDO


def test_situacao_desconhecida_nao_produz_mensagem() -> None:
    with pytest.raises(ValueError):
        mensagem_para("sintatico")
