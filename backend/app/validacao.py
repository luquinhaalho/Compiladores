"""Regras de aceitação do código-fonte antes de qualquer análise.

Nesta etapa o backend ainda não classifica erros léxicos, sintáticos ou
semânticos. Ele só distingue entrada vazia, entrada sem conteúdo útil e
texto que pode ser guardado para as próximas etapas.
"""

from app.mensagens import MENSAGEM_BRANCO, MENSAGEM_RECEBIDO, MENSAGEM_VAZIA


def classificar_codigo(codigo: str) -> str:
    """Classifica o texto em ``vazio``, ``branco`` ou ``aceito``."""
    if codigo == "":
        return "vazio"
    if codigo.strip() == "":
        return "branco"
    return "aceito"


def mensagem_para(situacao: str) -> str:
    if situacao == "vazio":
        return MENSAGEM_VAZIA
    if situacao == "branco":
        return MENSAGEM_BRANCO
    if situacao == "aceito":
        return MENSAGEM_RECEBIDO
    raise ValueError("situação desconhecida")
