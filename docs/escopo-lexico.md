# Escopo léxico do subconjunto Java

O scanner reconhece apenas o que esta tabela descreve. Um programa pode estar sintaticamente errado e, ainda assim, ser tokenizado: a estrutura fica para a etapa do parser.

| Categoria | Token | Formação e exemplos |
|---|---|---|
| Palavras reservadas | `PALAVRA_RESERVADA` | `int`, `double`, `boolean`, `true`, `false`. A comparação diferencia maiúsculas: `Int` é identificador. |
| Identificadores | `IDENTIFICADOR` | Letra ASCII ou `_`, seguida de letras ASCII, dígitos ou `_`. Exemplos: `numero`, `resultado`, `_x1`. Letras acentuadas não entram no identificador. |
| Literais inteiros | `LITERAL_INTEIRO` | Um ou mais dígitos: `10`, `0`, `42`, `007`. Não há notação octal nem hexadecimal. |
| Literais reais | `LITERAL_REAL` | Dígitos, ponto e dígitos: `2.5`, `10.0`. `10.` e `.5` são erros. Não há notação científica. |
| Operadores | `OPERADOR` | `+`, `-`, `*`, `/`, `=`. |
| Delimitadores | `DELIMITADOR` | `(`, `)`, `;`. |
| Comentário de linha | ignorado | `//` até o fim da linha. Não vira token. |
| Comentário de bloco | ignorado | `/*` até `*/`. Se não houver fechamento, é erro léxico. |
| Espaços | ignorados | Espaço, tabulação e quebras `\n` e `\r\n`. Não viram token. Tabulação conta como uma coluna. |
| Fora do subconjunto | `ERRO_LEXICO` | `@`, `#`, `$`, `<`, `>`, aspas, `==`, `!=`, `<=`, `>=`, `&&`, `\|\|`, `++`, `--` e cadeias entre aspas. |

O scanner acumula todos os erros e continua depois de cada um. A posição é a linha e a coluna em que o lexema começa, contadas a partir de 1.

Cadeias (`"texto"`) e caracteres (`'a'`) não são literais desta versão. O trecho inteiro, até a aspa de fechamento ou o fim da linha, vira um único erro explicando que aspas ainda não são reconhecidas.

`if`, `else`, `while`, `return`, chaves e operadores relacionais ficam de fora de propósito. Eles poderão entrar quando o subconjunto sintático crescer.
