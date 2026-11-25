"""Parser descendente recursivo do subconjunto didático de Java.

Cada não terminal da gramática (docs/gramatica.md) vira um método. A entrada
é a lista de tokens do scanner. Em caso de erro, apenas o primeiro diagnóstico
é guardado e a análise para.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ast_nodes import NoAST
from app.lexer import Token

TIPOS = frozenset({"int", "double", "boolean"})
BOOLEANOS = frozenset({"true", "false"})
EOF = Token("EOF", "", 0, 0)


@dataclass(frozen=True)
class ErroSintatico:
    tipo: str
    linha: int
    coluna: int
    encontrado: str
    esperado: list[str]
    mensagem: str
    regra: str | None = None


@dataclass(frozen=True)
class ResultadoSintatico:
    sucesso: bool
    ast: NoAST | None
    erros: list[ErroSintatico]
    executado: bool = True


class ErroParse(Exception):
    def __init__(self, erro: ErroSintatico) -> None:
        self.erro = erro
        super().__init__(erro.mensagem)


def analisar_sintatico(tokens: list[Token]) -> ResultadoSintatico:
    try:
        programa = _Parser(tokens).programa()
        return ResultadoSintatico(sucesso=True, ast=programa, erros=[])
    except ErroParse as falha:
        return ResultadoSintatico(sucesso=False, ast=None, erros=[falha.erro])


def mensagem_sintatica(resultado: ResultadoSintatico) -> str:
    if not resultado.executado:
        return (
            "A análise sintática não foi executada porque há erros léxicos. "
            "Corrija o vocabulário do programa antes de analisar a estrutura."
        )
    if resultado.sucesso:
        quantidade = len(resultado.ast.filhos) if resultado.ast else 0
        palavra = "statement" if quantidade == 1 else "statements"
        return (
            f"Análise sintática concluída. AST com {quantidade} {palavra}. "
            "A análise semântica ainda não está disponível nesta versão."
        )
    return (
        "A análise sintática encontrou um erro. "
        "A AST não foi produzida. "
        "A análise semântica ainda não está disponível nesta versão."
    )


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.indice = 0

    def programa(self) -> NoAST:
        statements: list[NoAST] = []
        inicio = self._atual()
        while not self._acabou():
            statements.append(self.statement())
        fim = self._anterior() if statements else inicio
        return NoAST(
            tipo="PROGRAMA",
            linha=inicio.linha if inicio.tipo != "EOF" else 1,
            coluna=inicio.coluna if inicio.tipo != "EOF" else 1,
            linha_fim=fim.linha if fim.tipo != "EOF" else 1,
            coluna_fim=self._coluna_fim(fim) if fim.tipo != "EOF" else 1,
            filhos=statements,
            regra="programa = { statement } ;",
        )

    def statement(self) -> NoAST:
        if self._eh_tipo():
            return self.var_decl()
        return self.expr_stmt()

    def var_decl(self) -> NoAST:
        regra = 'varDecl = tipo IDENTIFICADOR "=" expressao ";" ;'
        tipo_tok = self._consumir_tipo(regra)
        nome = self._consumir(
            "IDENTIFICADOR",
            ["identificador"],
            regra,
            "Após o tipo, a declaração exige o nome da variável.",
        )
        self._consumir_operador(
            "=",
            ["="],
            regra,
            "Após o identificador, a declaração exige '=' e uma expressão inicializadora.",
        )
        expressao = self.expressao()
        ponto = self._consumir(
            "DELIMITADOR",
            [";"],
            regra,
            "Toda declaração deve terminar com ';'.",
            lexema=";",
        )
        return NoAST(
            tipo="DECLARACAO_VARIAVEL",
            linha=tipo_tok.linha,
            coluna=tipo_tok.coluna,
            linha_fim=ponto.linha,
            coluna_fim=self._coluna_fim(ponto),
            atributos={"tipoDado": tipo_tok.lexema, "nome": nome.lexema},
            filhos=[expressao],
            regra=regra,
        )

    def expr_stmt(self) -> NoAST:
        regra = 'exprStmt = expressao ";" ;'
        inicio = self._atual()
        expressao = self.expressao()
        ponto = self._consumir(
            "DELIMITADOR",
            [";"],
            regra,
            "Uma expressão usada como statement deve terminar com ';'.",
            lexema=";",
        )
        return NoAST(
            tipo="EXPRESSAO_STMT",
            linha=inicio.linha,
            coluna=inicio.coluna,
            linha_fim=ponto.linha,
            coluna_fim=self._coluna_fim(ponto),
            filhos=[expressao],
            regra=regra,
        )

    def expressao(self) -> NoAST:
        return self.expressao_soma()

    def expressao_soma(self) -> NoAST:
        regra = 'expressao_soma = expressao_mult { ( "+" | "-" ) expressao_mult } ;'
        esquerda = self.expressao_mult()
        while self._eh_operador("+") or self._eh_operador("-"):
            operador = self._avancar()
            direita = self.expressao_mult()
            tipo = "ADICAO" if operador.lexema == "+" else "SUBTRACAO"
            esquerda = NoAST(
                tipo=tipo,
                linha=esquerda.linha,
                coluna=esquerda.coluna,
                linha_fim=direita.linha_fim,
                coluna_fim=direita.coluna_fim,
                atributos={"operador": operador.lexema},
                filhos=[esquerda, direita],
                regra=regra,
            )
        return esquerda

    def expressao_mult(self) -> NoAST:
        regra = 'expressao_mult = fator { ( "*" | "/" ) fator } ;'
        esquerda = self.fator()
        while self._eh_operador("*") or self._eh_operador("/"):
            operador = self._avancar()
            direita = self.fator()
            tipo = "MULTIPLICACAO" if operador.lexema == "*" else "DIVISAO"
            esquerda = NoAST(
                tipo=tipo,
                linha=esquerda.linha,
                coluna=esquerda.coluna,
                linha_fim=direita.linha_fim,
                coluna_fim=direita.coluna_fim,
                atributos={"operador": operador.lexema},
                filhos=[esquerda, direita],
                regra=regra,
            )
        return esquerda

    def fator(self) -> NoAST:
        regra = (
            'fator = LITERAL_INTEIRO | LITERAL_REAL | IDENTIFICADOR | '
            '"true" | "false" | "(" expressao ")" | "-" fator ;'
        )
        atual = self._atual()

        if self._eh_operador("-"):
            menos = self._avancar()
            operando = self.fator()
            return NoAST(
                tipo="NEGACAO",
                linha=menos.linha,
                coluna=menos.coluna,
                linha_fim=operando.linha_fim,
                coluna_fim=operando.coluna_fim,
                atributos={"operador": "-"},
                filhos=[operando],
                regra=regra,
            )

        if atual.tipo == "LITERAL_INTEIRO":
            tok = self._avancar()
            return self._folha("LITERAL_INTEIRO", tok, {"valor": tok.lexema}, regra)

        if atual.tipo == "LITERAL_REAL":
            tok = self._avancar()
            return self._folha("LITERAL_REAL", tok, {"valor": tok.lexema}, regra)

        if atual.tipo == "IDENTIFICADOR":
            tok = self._avancar()
            return self._folha("IDENTIFICADOR", tok, {"nome": tok.lexema}, regra)

        if atual.tipo == "PALAVRA_RESERVADA" and atual.lexema in BOOLEANOS:
            tok = self._avancar()
            return self._folha("LITERAL_BOOLEANO", tok, {"valor": tok.lexema}, regra)

        if atual.tipo == "DELIMITADOR" and atual.lexema == "(":
            abre = self._avancar()
            expressao = self.expressao()
            fecha = self._consumir(
                "DELIMITADOR",
                [")"],
                regra,
                "Era esperado ')' para fechar a expressão entre parênteses.",
                lexema=")",
            )
            expressao.linha = abre.linha
            expressao.coluna = abre.coluna
            expressao.linha_fim = fecha.linha
            expressao.coluna_fim = self._coluna_fim(fecha)
            expressao.regra = regra
            return expressao

        self._falhar(
            ["literal", "identificador", "true", "false", "(", "-"],
            regra,
            "Era esperado um fator (literal, identificador, true, false, "
            "expressão entre parênteses ou '-' unário).",
        )

    def _folha(
        self, tipo: str, token: Token, atributos: dict, regra: str
    ) -> NoAST:
        return NoAST(
            tipo=tipo,
            linha=token.linha,
            coluna=token.coluna,
            linha_fim=token.linha,
            coluna_fim=self._coluna_fim(token),
            atributos=atributos,
            regra=regra,
        )

    def _eh_tipo(self) -> bool:
        atual = self._atual()
        return atual.tipo == "PALAVRA_RESERVADA" and atual.lexema in TIPOS

    def _eh_operador(self, lexema: str) -> bool:
        atual = self._atual()
        return atual.tipo == "OPERADOR" and atual.lexema == lexema

    def _consumir_tipo(self, regra: str) -> Token:
        atual = self._atual()
        if atual.tipo == "PALAVRA_RESERVADA" and atual.lexema in TIPOS:
            return self._avancar()
        self._falhar(
            ["int", "double", "boolean"],
            regra,
            "Uma declaração começa com o tipo da variável (int, double ou boolean).",
        )

    def _consumir_operador(
        self, lexema: str, esperado: list[str], regra: str, dica: str
    ) -> Token:
        atual = self._atual()
        if atual.tipo == "OPERADOR" and atual.lexema == lexema:
            return self._avancar()
        self._falhar(esperado, regra, dica)

    def _consumir(
        self,
        tipo: str,
        esperado: list[str],
        regra: str,
        dica: str,
        lexema: str | None = None,
    ) -> Token:
        atual = self._atual()
        if atual.tipo == tipo and (lexema is None or atual.lexema == lexema):
            return self._avancar()
        self._falhar(esperado, regra, dica)

    def _falhar(self, esperado: list[str], regra: str, dica: str) -> None:
        atual = self._atual()
        if atual.tipo == "EOF":
            encontrado = "fim do código"
            mensagem = (
                f"Erro sintático: o código terminou antes de concluir a construção. "
                f"{dica} Regra: {regra}"
            )
            linha = self._anterior().linha if self.indice else 1
            coluna = self._coluna_fim(self._anterior()) if self.indice else 1
        else:
            encontrado = atual.lexema
            mensagem = (
                f"Erro sintático na linha {atual.linha}, coluna {atual.coluna}: "
                f"era esperado {self._listar(esperado)}, mas foi encontrado '{encontrado}'. "
                f"{dica} Regra: {regra}"
            )
            linha = atual.linha
            coluna = atual.coluna
        raise ErroParse(
            ErroSintatico(
                tipo="ERRO_SINTATICO",
                linha=linha,
                coluna=coluna,
                encontrado=encontrado,
                esperado=esperado,
                mensagem=mensagem,
                regra=regra,
            )
        )

    def _listar(self, itens: list[str]) -> str:
        citados = [f"'{item}'" for item in itens]
        if len(citados) == 1:
            return citados[0]
        return ", ".join(citados[:-1]) + " ou " + citados[-1]

    def _atual(self) -> Token:
        if self.indice >= len(self.tokens):
            if self.tokens:
                ultimo = self.tokens[-1]
                return Token("EOF", "", ultimo.linha, self._coluna_fim(ultimo))
            return EOF
        return self.tokens[self.indice]

    def _anterior(self) -> Token:
        if self.indice == 0:
            return EOF
        return self.tokens[self.indice - 1]

    def _avancar(self) -> Token:
        token = self._atual()
        if not self._acabou():
            self.indice += 1
        return token

    def _acabou(self) -> bool:
        return self.indice >= len(self.tokens)

    def _coluna_fim(self, token: Token) -> int:
        if token.tipo == "EOF":
            return token.coluna or 1
        return token.coluna + max(len(token.lexema), 1) - 1
