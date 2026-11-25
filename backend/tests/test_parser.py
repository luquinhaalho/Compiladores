from app.lexer import analisar_lexico
from app.parser import analisar_sintatico


def _parse(codigo: str):
    lexico = analisar_lexico(codigo)
    assert lexico.sucesso, [erro.mensagem for erro in lexico.erros]
    return analisar_sintatico(lexico.tokens)


def _tipos_arvore(no) -> list:
    return [no.tipo] + [item for filho in no.filhos for item in _tipos_arvore(filho)]


def test_declaracao_simples() -> None:
    resultado = _parse("int numero = 10;")
    assert resultado.sucesso is True
    assert resultado.ast is not None
    assert resultado.ast.tipo == "PROGRAMA"
    assert len(resultado.ast.filhos) == 1
    decl = resultado.ast.filhos[0]
    assert decl.tipo == "DECLARACAO_VARIAVEL"
    assert decl.atributos == {"tipoDado": "int", "nome": "numero"}
    assert decl.filhos[0].tipo == "LITERAL_INTEIRO"
    assert decl.filhos[0].atributos["valor"] == "10"


def test_precedencia_multiplicacao_sobre_adicao() -> None:
    resultado = _parse("int resultado = 10 + 5 * 2;")
    expr = resultado.ast.filhos[0].filhos[0]
    assert expr.tipo == "ADICAO"
    assert expr.filhos[0].atributos["valor"] == "10"
    assert expr.filhos[1].tipo == "MULTIPLICACAO"
    assert expr.filhos[1].filhos[0].atributos["valor"] == "5"
    assert expr.filhos[1].filhos[1].atributos["valor"] == "2"


def test_associatividade_esquerda_da_subtracao() -> None:
    resultado = _parse("int resultado = 20 - 5 - 3;")
    expr = resultado.ast.filhos[0].filhos[0]
    assert expr.tipo == "SUBTRACAO"
    assert expr.filhos[0].tipo == "SUBTRACAO"
    assert expr.filhos[0].filhos[0].atributos["valor"] == "20"
    assert expr.filhos[0].filhos[1].atributos["valor"] == "5"
    assert expr.filhos[1].atributos["valor"] == "3"


def test_parenteses_alteram_a_arvore() -> None:
    resultado = _parse("int resultado = (10 + 5) * 2;")
    expr = resultado.ast.filhos[0].filhos[0]
    assert expr.tipo == "MULTIPLICACAO"
    assert expr.filhos[0].tipo == "ADICAO"
    assert expr.filhos[1].atributos["valor"] == "2"


def test_varias_declaracoes_e_booleano() -> None:
    codigo = "int total = 8;\ndouble media = total / 2.0;\nboolean ativo = true;\n"
    resultado = _parse(codigo)
    assert resultado.sucesso is True
    assert [filho.tipo for filho in resultado.ast.filhos] == [
        "DECLARACAO_VARIAVEL",
        "DECLARACAO_VARIAVEL",
        "DECLARACAO_VARIAVEL",
    ]
    assert resultado.ast.filhos[2].atributos["tipoDado"] == "boolean"
    assert resultado.ast.filhos[2].filhos[0].tipo == "LITERAL_BOOLEANO"


def test_expressao_como_statement() -> None:
    resultado = _parse("1 + 2;")
    assert resultado.ast.filhos[0].tipo == "EXPRESSAO_STMT"
    assert resultado.ast.filhos[0].filhos[0].tipo == "ADICAO"


def test_negacao_unaria() -> None:
    resultado = _parse("int x = -3 * 2;")
    expr = resultado.ast.filhos[0].filhos[0]
    assert expr.tipo == "MULTIPLICACAO"
    assert expr.filhos[0].tipo == "NEGACAO"
    assert expr.filhos[0].filhos[0].atributos["valor"] == "3"


def test_falta_ponto_e_virgula() -> None:
    resultado = _parse("int numero = 10")
    assert resultado.sucesso is False
    assert resultado.ast is None
    erro = resultado.erros[0]
    assert erro.tipo == "ERRO_SINTATICO"
    assert ";" in erro.esperado
    assert "fim do código" in erro.encontrado
    assert "Regra:" in erro.mensagem
    assert erro.regra is not None


def test_falta_identificador_na_declaracao() -> None:
    resultado = _parse("int = 10;")
    assert resultado.sucesso is False
    erro = resultado.erros[0]
    assert "identificador" in erro.esperado
    assert erro.encontrado == "="
    assert erro.linha == 1


def test_fator_incompleto() -> None:
    resultado = _parse("10 + ;")
    assert resultado.sucesso is False
    erro = resultado.erros[0]
    assert erro.encontrado == ";"
    assert "fator" in erro.mensagem.lower() or "literal" in erro.esperado[0]


def test_parentese_nao_fechado() -> None:
    resultado = _parse("int x = (1 + 2;")
    assert resultado.sucesso is False
    erro = resultado.erros[0]
    assert ")" in erro.esperado
    assert erro.encontrado == ";"


def test_apenas_o_primeiro_erro_e_reportado() -> None:
    resultado = _parse("int = 10; int = 20;")
    assert len(resultado.erros) == 1


def test_programa_vazio_de_tokens_produz_ast_vazia() -> None:
    resultado = analisar_sintatico([])
    assert resultado.sucesso is True
    assert resultado.ast.tipo == "PROGRAMA"
    assert resultado.ast.filhos == []


def test_posicoes_da_declaracao() -> None:
    resultado = _parse("int numero = 10;")
    decl = resultado.ast.filhos[0]
    assert decl.linha == 1
    assert decl.coluna == 1
    assert decl.linha_fim == 1
    assert decl.coluna_fim == 16
