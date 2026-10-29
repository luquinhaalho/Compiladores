import pytest

from app.lexer import PALAVRAS_RESERVADAS, analisar_lexico, mensagem_analise


def _tipos(codigo: str) -> list[tuple[str, str]]:
    resultado = analisar_lexico(codigo)
    assert resultado.erros == []
    return [(token.tipo, token.lexema) for token in resultado.tokens]


def test_declaracao_inteira_com_posicoes() -> None:
    resultado = analisar_lexico("int numero = 10;")

    assert [(token.tipo, token.lexema, token.linha, token.coluna) for token in resultado.tokens] == [
        ("PALAVRA_RESERVADA", "int", 1, 1),
        ("IDENTIFICADOR", "numero", 1, 5),
        ("OPERADOR", "=", 1, 12),
        ("LITERAL_INTEIRO", "10", 1, 14),
        ("DELIMITADOR", ";", 1, 16),
    ]
    assert resultado.sucesso is True


@pytest.mark.parametrize("palavra", sorted(PALAVRAS_RESERVADAS))
def test_cada_palavra_reservada(palavra: str) -> None:
    assert _tipos(palavra) == [("PALAVRA_RESERVADA", palavra)]


def test_palavra_reservada_diferencia_maiusculas() -> None:
    assert _tipos("Int") == [("IDENTIFICADOR", "Int")]


@pytest.mark.parametrize("nome", ["numero", "resultado", "_x1", "a1", "_"])
def test_identificadores_validos(nome: str) -> None:
    assert _tipos(nome) == [("IDENTIFICADOR", nome)]


@pytest.mark.parametrize(
    ("codigo", "tipo", "lexema"),
    [
        ("10", "LITERAL_INTEIRO", "10"),
        ("0", "LITERAL_INTEIRO", "0"),
        ("42", "LITERAL_INTEIRO", "42"),
        ("007", "LITERAL_INTEIRO", "007"),
        ("2.5", "LITERAL_REAL", "2.5"),
        ("10.0", "LITERAL_REAL", "10.0"),
    ],
)
def test_literais_numericos(codigo: str, tipo: str, lexema: str) -> None:
    assert _tipos(codigo) == [(tipo, lexema)]


@pytest.mark.parametrize("operador", ["+", "-", "*", "/", "="])
def test_operadores_simples(operador: str) -> None:
    assert _tipos(operador) == [("OPERADOR", operador)]


@pytest.mark.parametrize("delimitador", ["(", ")", ";"])
def test_delimitadores(delimitador: str) -> None:
    assert _tipos(delimitador) == [("DELIMITADOR", delimitador)]


@pytest.mark.parametrize("sequencia", ["==", "!=", "<=", ">=", "&&", "||", "++", "--"])
def test_operadores_compostos_viram_erro(sequencia: str) -> None:
    resultado = analisar_lexico(sequencia)

    assert resultado.tokens == []
    assert len(resultado.erros) == 1
    erro = resultado.erros[0]
    assert erro.lexema == sequencia
    assert erro.linha == 1
    assert erro.coluna == 1
    assert "não faz parte do subconjunto" in erro.mensagem


def test_comentario_de_linha_e_ignorado() -> None:
    codigo = 'int a = 1; // "ação" <>&\n'
    assert _tipos(codigo) == [
        ("PALAVRA_RESERVADA", "int"),
        ("IDENTIFICADOR", "a"),
        ("OPERADOR", "="),
        ("LITERAL_INTEIRO", "1"),
        ("DELIMITADOR", ";"),
    ]


def test_comentario_de_bloco_pula_linhas() -> None:
    codigo = "/* bloco\ncom linha */ int x = 1;"
    resultado = analisar_lexico(codigo)

    assert resultado.erros == []
    inteiro = resultado.tokens[-2]
    assert resultado.tokens[0].lexema == "int"
    assert resultado.tokens[0].linha == 2
    assert resultado.tokens[0].coluna == 14
    assert inteiro.lexema == "1"


def test_comentario_de_bloco_nao_fechado() -> None:
    resultado = analisar_lexico("/* opa")

    assert resultado.tokens == []
    assert len(resultado.erros) == 1
    erro = resultado.erros[0]
    assert erro.lexema == "/* opa"
    assert "não foi fechado" in erro.mensagem
    assert "linha 1, coluna 1" in erro.mensagem


def test_espacos_nao_geram_tokens_e_atualizam_a_posicao() -> None:
    resultado = analisar_lexico(" \n\t int")

    assert resultado.erros == []
    assert len(resultado.tokens) == 1
    token = resultado.tokens[0]
    assert token.lexema == "int"
    assert token.linha == 2
    assert token.coluna == 3


def test_caractere_nao_reconhecido_informa_posicao_e_segue() -> None:
    resultado = analisar_lexico("a @ b")

    assert [(token.lexema) for token in resultado.tokens] == ["a", "b"]
    assert len(resultado.erros) == 1
    erro = resultado.erros[0]
    assert erro.tipo == "ERRO_LEXICO"
    assert erro.lexema == "@"
    assert erro.linha == 1
    assert erro.coluna == 3
    assert erro.mensagem == (
        "Erro léxico na linha 1, coluna 3: caractere não reconhecido '@'. "
        "Verifique se ele faz parte do subconjunto suportado."
    )


def test_aspas_explicam_que_cadeias_estao_fora_do_subconjunto() -> None:
    resultado = analisar_lexico('"oi"')

    assert resultado.tokens == []
    assert len(resultado.erros) == 1
    assert resultado.erros[0].lexema == '"oi"'
    assert "Cadeias e caracteres entre aspas" in resultado.erros[0].mensagem


def test_literal_real_malformado() -> None:
    sem_fracao = analisar_lexico("10.")
    assert sem_fracao.tokens == []
    assert sem_fracao.erros[0].lexema == "10."
    assert "literal real malformado" in sem_fracao.erros[0].mensagem

    sem_inteiro = analisar_lexico(".5")
    assert sem_inteiro.tokens == []
    assert sem_inteiro.erros[0].lexema == ".5"


def test_numero_colado_em_identificador_sao_dois_tokens() -> None:
    assert _tipos("1abc") == [
        ("LITERAL_INTEIRO", "1"),
        ("IDENTIFICADOR", "abc"),
    ]


def test_codigo_vazio_so_espacos_e_so_comentario() -> None:
    for codigo in ("", " \n\t ", "// apenas", "/* bloco */"):
        resultado = analisar_lexico(codigo)
        assert resultado.tokens == []
        assert resultado.erros == []
        assert resultado.sucesso is True


def test_token_no_fim_do_arquivo_sem_quebra_de_linha() -> None:
    resultado = analisar_lexico("int a = 1;")
    assert resultado.tokens[-1].lexema == ";"
    assert resultado.sucesso is True


def test_varios_erros_sao_acumulados() -> None:
    resultado = analisar_lexico("a @ b # c")
    assert [token.lexema for token in resultado.tokens] == ["a", "b", "c"]
    assert [erro.lexema for erro in resultado.erros] == ["@", "#"]


def test_mensagem_distingue_sucesso_comentario_e_erro() -> None:
    ok = analisar_lexico("int a = 1;")
    vazio = analisar_lexico("// nada")
    ruim = analisar_lexico("@")

    assert mensagem_analise(ok).startswith("Análise léxica concluída. 5 tokens")
    assert "Nenhum token foi produzido" in mensagem_analise(vazio)
    assert "1 erro léxico" in mensagem_analise(ruim)
    assert "sintática ainda não está disponível" in mensagem_analise(ok)
