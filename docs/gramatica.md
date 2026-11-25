# Gramática do subconjunto didático de Java

Esta gramática descreve o que o parser da Etapa 4 reconhece. Ela é coerente com o scanner documentado em [escopo-lexico.md](escopo-lexico.md): todo terminal abaixo corresponde a um token produzido pelo analisador léxico.

## Estratégia do parser

- Abordagem: **descendente recursivo** (Recursive Descent), escrita à mão em Python (`backend/app/parser.py`).
- Justificativa: o subconjunto é pequeno; cada não terminal vira uma função legível, o que facilita explicar a análise a um estudante e a construção da AST.
- Ferramentas externas: nenhuma (sem ANTLR, Lark, PLY ou Bison).
- Entrada: lista de tokens do scanner da Etapa 3.
- Decisão sobre erros léxicos: se o scanner reportar qualquer erro, **o parser não é executado**. Tokens inválidos gerariam diagnósticos sintáticos sem sentido. Os erros léxicos continuam sendo apresentados.
- Recuperação de erros: apenas o **primeiro** erro sintático é reportado. Não há modo pânico nesta versão.

## Símbolo inicial

`programa`

## Terminais (tokens do scanner)

| Terminal gramatical | Token do scanner | Lexemas |
|---|---|---|
| tipo | `PALAVRA_RESERVADA` | `int`, `double`, `boolean` |
| true / false | `PALAVRA_RESERVADA` | `true`, `false` |
| IDENTIFICADOR | `IDENTIFICADOR` | nomes |
| LITERAL_INTEIRO | `LITERAL_INTEIRO` | dígitos |
| LITERAL_REAL | `LITERAL_REAL` | dígitos.dígitos |
| `+` `-` `*` `/` `=` | `OPERADOR` | os mesmos |
| `(` `)` `;` | `DELIMITADOR` | os mesmos |

Espaços e comentários não aparecem na gramática: o scanner já os descarta.

## Não terminais

`programa`, `statement`, `varDecl`, `tipo`, `exprStmt`, `expressao`, `expressao_soma`, `expressao_mult`, `fator`

## Gramática em EBNF

```ebnf
programa         = { statement } ;
statement        = varDecl | exprStmt ;
varDecl          = tipo IDENTIFICADOR "=" expressao ";" ;
tipo             = "int" | "double" | "boolean" ;
exprStmt         = expressao ";" ;
expressao        = expressao_soma ;
expressao_soma   = expressao_mult { ( "+" | "-" ) expressao_mult } ;
expressao_mult   = fator { ( "*" | "/" ) fator } ;
fator            = LITERAL_INTEIRO
                 | LITERAL_REAL
                 | IDENTIFICADOR
                 | "true"
                 | "false"
                 | "(" expressao ")"
                 | "-" fator ;
```

## Precedência e associatividade

| Nível | Operadores | Associatividade |
|---|---|---|
| 1 (maior) | unário `-` | direita |
| 2 | `*` `/` | esquerda |
| 3 (menor) | `+` `-` | esquerda |

Parênteses alteram a organização. Exemplos:

```java
int resultado = 10 + 5 * 2;   // 10 + (5 * 2)
int resultado = 20 - 5 - 3;   // (20 - 5) - 3
int resultado = (10 + 5) * 2; // parênteses alteram a árvore
```

## Construções suportadas

- Declaração de variável com tipo, nome, `=` e expressão inicializadora.
- Expressão seguida de `;` (statement de expressão).
- Expressões aritméticas com `+`, `-`, `*`, `/`, unário `-` e parênteses.
- Literais inteiros, reais e booleanos (`true` / `false`).
- Uso de identificadores em expressões (sem verificação de declaração: isso é semântica, Etapa 5).
- Sequência de várias declarações ou expressões no programa.

## Fora do escopo

- `if`, `else`, `while`, `for`, `return`, métodos e classes.
- Chaves `{` `}`, vírgulas, operadores relacionais e lógicos.
- Declaração sem inicializador (`int x;`).
- Atribuição isolada depois da declaração (`x = 1;` como comando de atribuição dedicado): nesta gramática, `x = 1;` **não** é válida; um statement de expressão começa por um fator, não por atribuição. Use `int x = 1;` ou uma expressão como `x + 1;`.
- Análise semântica (tipos, variável não declarada).

## AST versus árvore de derivação

O sistema exibe a **Árvore Sintática Abstrata (AST)**: nós como `DECLARACAO_VARIAVEL`, `ADICAO` e `LITERAL_INTEIRO`, sem nós intermediários da gramática (`expressao_soma`, `fator`). A árvore de derivação concreta, com todos os não terminais, não é exibida nesta versão.

## Tipos de nó da AST

| Tipo | Significado | Atributos principais | Filhos |
|---|---|---|---|
| `PROGRAMA` | sequência de statements | — | statements |
| `DECLARACAO_VARIAVEL` | declaração com inicializador | `tipoDado`, `nome` | expressão |
| `EXPRESSAO_STMT` | expressão seguida de `;` | — | expressão |
| `IDENTIFICADOR` | nome | `nome` | — |
| `LITERAL_INTEIRO` | inteiro | `valor` | — |
| `LITERAL_REAL` | real | `valor` | — |
| `LITERAL_BOOLEANO` | `true`/`false` | `valor` | — |
| `ADICAO` / `SUBTRACAO` / `MULTIPLICACAO` / `DIVISAO` | operação binária | `operador` | esquerda, direita |
| `NEGACAO` | unário `-` | `operador` | operando |

Todo nó carrega `linha`, `coluna`, `linhaFim`, `colunaFim` e, quando útil, `regra` (produção EBNF reconhecida).

## Exemplos

Válido:

```java
int resultado = 10 + 5 * 2;
double media = total / 2.0;
boolean ativo = true;
```

Inválidos (erro sintático intencional):

```java
int numero = 10          // falta ;
int = 10;                // falta identificador
10 + ;                   // fator incompleto
int x = (1 + 2;          // falta )
```
