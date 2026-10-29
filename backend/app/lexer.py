"""Scanner do subconjunto didático de Java.

O analisador percorre o texto caractere a caractere, sem gerador externo.
O subconjunto é pequeno o bastante para o laço ficar legível por um estudante
e servir de base ao parser da etapa seguinte. Espaços e comentários são
descartados. Um erro não interrompe o restante da varredura.
"""

from dataclasses import dataclass


PALAVRAS_RESERVADAS = frozenset({"int", "double", "boolean", "true", "false"})
OPERADORES = frozenset("+-*/=")
DELIMITADORES = frozenset("();")
COMPOSTOS_NAO_SUPORTADOS = ("==", "!=", "<=", ">=", "&&", "||", "++", "--")


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int


@dataclass(frozen=True)
class ErroLexico:
    tipo: str
    lexema: str
    linha: int
    coluna: int
    mensagem: str


@dataclass(frozen=True)
class ResultadoLexico:
    tokens: list[Token]
    erros: list[ErroLexico]

    @property
    def sucesso(self) -> bool:
        return not self.erros


def mensagem_analise(resultado: ResultadoLexico) -> str:
    """Resume o que o scanner fez, sem antecipar a análise sintática."""
    quantidade_tokens = len(resultado.tokens)
    quantidade_erros = len(resultado.erros)
    limite = "A análise sintática ainda não está disponível nesta versão."
    if quantidade_erros:
        palavra = "erro léxico" if quantidade_erros == 1 else "erros léxicos"
        return (
            f"A análise léxica encontrou {quantidade_erros} {palavra}. "
            "Os trechos válidos foram tokenizados mesmo assim. "
            + limite
        )
    if quantidade_tokens == 0:
        return (
            "Análise léxica concluída. Nenhum token foi produzido: "
            "o texto contém apenas espaços ou comentários. "
            + limite
        )
    palavra = "token" if quantidade_tokens == 1 else "tokens"
    return (
        f"Análise léxica concluída. {quantidade_tokens} {palavra} reconhecidos. "
        + limite
    )


def analisar_lexico(codigo: str) -> ResultadoLexico:
    return _Scanner(codigo).executar()


class _Scanner:
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        self.tamanho = len(codigo)
        self.indice = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: list[Token] = []
        self.erros: list[ErroLexico] = []

    def executar(self) -> ResultadoLexico:
        while self.indice < self.tamanho:
            if self._espaco():
                self._avancar()
                continue
            if self._comentario():
                continue
            if self._inicio_de_identificador(self._olhar()):
                self._identificador()
                continue
            if self._olhar().isdigit():
                self._numero()
                continue
            if self._olhar() == ".":
                self._ponto()
                continue
            composto = self._composto_nao_suportado()
            if composto:
                self._erro_composto(composto)
                continue
            atual = self._olhar()
            if atual in OPERADORES:
                self._token_simples("OPERADOR")
                continue
            if atual in DELIMITADORES:
                self._token_simples("DELIMITADOR")
                continue
            if atual in {'"', "'"}:
                self._aspas()
                continue
            self._erro_caractere()
        return ResultadoLexico(self.tokens, self.erros)

    def _olhar(self, distancia: int = 0) -> str:
        posicao = self.indice + distancia
        if posicao >= self.tamanho:
            return ""
        return self.codigo[posicao]

    def _avancar(self) -> str:
        caractere = self.codigo[self.indice]
        self.indice += 1
        if caractere == "\r":
            if self._olhar() == "\n":
                self.indice += 1
            self.linha += 1
            self.coluna = 1
            return caractere
        if caractere == "\n":
            self.linha += 1
            self.coluna = 1
            return caractere
        self.coluna += 1
        return caractere

    def _espaco(self) -> bool:
        return self._olhar() in " \t\r\n"

    def _comentario(self) -> bool:
        if self._olhar() != "/":
            return False
        if self._olhar(1) == "/":
            self._avancar()
            self._avancar()
            while self._olhar() and self._olhar() not in "\r\n":
                self._avancar()
            return True
        if self._olhar(1) == "*":
            linha = self.linha
            coluna = self.coluna
            inicio = self.indice
            self._avancar()
            self._avancar()
            while self._olhar():
                if self._olhar() == "*" and self._olhar(1) == "/":
                    self._avancar()
                    self._avancar()
                    return True
                self._avancar()
            lexema = self.codigo[inicio : self.indice]
            self.erros.append(
                ErroLexico(
                    tipo="ERRO_LEXICO",
                    lexema=lexema,
                    linha=linha,
                    coluna=coluna,
                    mensagem=(
                        f"Erro léxico na linha {linha}, coluna {coluna}: "
                        "comentário de bloco iniciado por '/*' não foi fechado com '*/'."
                    ),
                )
            )
            return True
        return False

    def _inicio_de_identificador(self, caractere: str) -> bool:
        return bool(caractere) and caractere.isascii() and (
            caractere.isalpha() or caractere == "_"
        )

    def _identificador(self) -> None:
        linha = self.linha
        coluna = self.coluna
        inicio = self.indice
        self._avancar()
        while self._continuacao_de_identificador(self._olhar()):
            self._avancar()
        lexema = self.codigo[inicio : self.indice]
        tipo = "PALAVRA_RESERVADA" if lexema in PALAVRAS_RESERVADAS else "IDENTIFICADOR"
        self.tokens.append(Token(tipo, lexema, linha, coluna))

    def _continuacao_de_identificador(self, caractere: str) -> bool:
        return bool(caractere) and caractere.isascii() and (
            caractere.isalnum() or caractere == "_"
        )

    def _numero(self) -> None:
        linha = self.linha
        coluna = self.coluna
        inicio = self.indice
        while self._olhar().isdigit():
            self._avancar()
        if self._olhar() == "." and self._olhar(1).isdigit():
            self._avancar()
            while self._olhar().isdigit():
                self._avancar()
            self.tokens.append(
                Token("LITERAL_REAL", self.codigo[inicio : self.indice], linha, coluna)
            )
            return
        if self._olhar() == ".":
            self._avancar()
            lexema = self.codigo[inicio : self.indice]
            self.erros.append(self._erro_real(lexema, linha, coluna))
            return
        self.tokens.append(
            Token("LITERAL_INTEIRO", self.codigo[inicio : self.indice], linha, coluna)
        )

    def _ponto(self) -> None:
        linha = self.linha
        coluna = self.coluna
        inicio = self.indice
        self._avancar()
        if self._olhar().isdigit():
            while self._olhar().isdigit():
                self._avancar()
            lexema = self.codigo[inicio : self.indice]
            self.erros.append(self._erro_real(lexema, linha, coluna))
            return
        self.erros.append(
            self._erro_de_caractere(".", linha, coluna)
        )

    def _composto_nao_suportado(self) -> str:
        par = self._olhar() + self._olhar(1)
        if par in COMPOSTOS_NAO_SUPORTADOS:
            return par
        return ""

    def _erro_composto(self, lexema: str) -> None:
        linha = self.linha
        coluna = self.coluna
        self._avancar()
        self._avancar()
        self.erros.append(
            ErroLexico(
                tipo="ERRO_LEXICO",
                lexema=lexema,
                linha=linha,
                coluna=coluna,
                mensagem=(
                    f"Erro léxico na linha {linha}, coluna {coluna}: "
                    f"a sequência '{lexema}' não faz parte do subconjunto. "
                    "Este scanner reconhece apenas os operadores + - * / =."
                ),
            )
        )

    def _token_simples(self, tipo: str) -> None:
        linha = self.linha
        coluna = self.coluna
        lexema = self._avancar()
        self.tokens.append(Token(tipo, lexema, linha, coluna))

    def _aspas(self) -> None:
        linha = self.linha
        coluna = self.coluna
        inicio = self.indice
        abre = self._avancar()
        while self._olhar() and self._olhar() not in "\r\n":
            if self._avancar() == abre:
                break
        lexema = self.codigo[inicio : self.indice]
        self.erros.append(
            ErroLexico(
                tipo="ERRO_LEXICO",
                lexema=lexema,
                linha=linha,
                coluna=coluna,
                mensagem=(
                    f"Erro léxico na linha {linha}, coluna {coluna}: "
                    f"sequência '{lexema}' não faz parte do subconjunto. "
                    "Cadeias e caracteres entre aspas ainda não são reconhecidos."
                ),
            )
        )

    def _erro_caractere(self) -> None:
        linha = self.linha
        coluna = self.coluna
        lexema = self._avancar()
        self.erros.append(self._erro_de_caractere(lexema, linha, coluna))

    def _erro_de_caractere(self, lexema: str, linha: int, coluna: int) -> ErroLexico:
        complemento = "Verifique se ele faz parte do subconjunto suportado."
        return ErroLexico(
            tipo="ERRO_LEXICO",
            lexema=lexema,
            linha=linha,
            coluna=coluna,
            mensagem=(
                f"Erro léxico na linha {linha}, coluna {coluna}: "
                f"caractere não reconhecido '{lexema}'. {complemento}"
            ),
        )

    def _erro_real(self, lexema: str, linha: int, coluna: int) -> ErroLexico:
        return ErroLexico(
            tipo="ERRO_LEXICO",
            lexema=lexema,
            linha=linha,
            coluna=coluna,
            mensagem=(
                f"Erro léxico na linha {linha}, coluna {coluna}: "
                f"literal real malformado '{lexema}'. "
                "O subconjunto exige dígitos antes e depois do ponto."
            ),
        )
