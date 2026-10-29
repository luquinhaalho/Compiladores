# Compiladores — visualização de AST

Software educacional para experimentar, em etapas, a geração e a visualização de árvores de sintaxe abstrata (AST). Nesta versão o estudante escreve ou escolhe um programa em um subconjunto de Java, pede a análise e vê os tokens reconhecidos pelo scanner. A análise sintática e a semântica ainda não são feitas.

## Linguagem e subconjunto didático

A linguagem analisada é **Java**.

O recorte não é a linguagem inteira. O subconjunto didático cobre:

- declaração de variáveis com tipo, nome e inicializador;
- expressões aritméticas com literais, identificadores, parênteses e os operadores `+`, `-`, `*` e `/`.

Gramática prevista, em EBNF:

```ebnf
program     = { statement } ;
statement   = varDecl | exprStmt ;
varDecl     = type identifier "=" expression ";" ;
exprStmt    = expression ";" ;
type        = "int" | "double" | "boolean" ;
expression  = term { ("+" | "-") term } ;
term        = factor { ("*" | "/") factor } ;
factor      = number | identifier | "(" expression ")" | "-" factor ;
```

Java foi escolhida porque é uma linguagem orientada a objetos com sintaxe rica. Tipos, declarações e operadores produzem nós de naturezas diferentes na AST, o que ajuda a separar árvore concreta e árvore abstrata. O subconjunto começa pequeno para que cada fase do compilador possa ser estudada isoladamente.

O vocabulário que o scanner reconhece está em [docs/escopo-lexico.md](docs/escopo-lexico.md). Em resumo:

| Categoria | Exemplos |
|---|---|
| Palavras reservadas | `int`, `double`, `boolean`, `true`, `false` |
| Identificadores | `numero`, `resultado`, `_x1` |
| Literais | `10`, `0`, `2.5` |
| Operadores | `+`, `-`, `*`, `/`, `=` |
| Delimitadores | `(`, `)`, `;` |
| Comentários, ignorados | `// linha` e `/* bloco */` |

## Scanner

O analisador léxico está em `backend/app/lexer.py`. É um laço escrito em Python, no mesmo processo do FastAPI, sem gerador nem dependência nova. O subconjunto cabe em um único módulo, e o estudante pode ler a varredura caractere a caractere antes de partir para o parser.

Cada token traz `tipo`, `lexema`, `linha` e `coluna`. Espaços e comentários fechados não viram token. Um caractere ou uma sequência fora do subconjunto gera `ERRO_LEXICO` com uma mensagem didática, e a leitura continua. Um programa sintaticamente inválido, mas formado por tokens conhecidos, é tokenizado normalmente.

## O que a interface faz

A tela em [http://localhost:3000](http://localhost:3000) identifica o laboratório e a linguagem Java. Ela oferece:

- um campo monoespaçado para escrever, colar e editar o código-fonte;
- uma lista de exemplos, que substituem o texto do campo e podem ser editados depois;
- o botão **Analisar**, que envia o código ao backend e aciona o scanner;
- a mensagem de validação ou de falha de comunicação;
- a contagem por categoria, o código com os lexemas coloridos, um passo a passo e a tabela de tokens;
- a lista de erros léxicos, com linha e coluna.

O código permanece no campo depois do envio. A tabela explica a diferença entre token e lexema, e os botões **Passo anterior** e **Próximo passo** percorrem a varredura na ordem em que o scanner encontrou cada trecho. Em telas estreitas, a tabela rola na horizontal.

### Exemplos disponíveis

| Exemplo | Código | Construção demonstrada |
|---|---|---|
| Declaração e inicialização | `int numero = 10;` | Palavra reservada, identificador, atribuição, inteiro e `;` |
| Expressão aritmética | `int resultado = (10 + 5) * 2;` | Soma, multiplicação e parênteses |
| Duas declarações | `int total = 8;` e `double media = total / 2.0;` | Dois tipos, divisão e literal real |
| Comentário e boolean | `boolean ativo = true;` | Comentário de linha ignorado e as palavras `boolean` e `true` |
| Erro léxico proposital | `int valor = 10 @ 2;` | O `@` vira erro e os demais tokens continuam na tabela |

Os textos ficam em `frontend/public/examples.json`. Estruturas condicionais ficam de fora porque ainda não pertencem ao subconjunto.

## Tecnologias

| Parte | Tecnologia |
|---|---|
| Frontend | HTML, CSS e JavaScript, servidos por Nginx |
| Backend | Python 3.12, FastAPI e o scanner em `app/lexer.py` |
| Testes da API | pytest |
| Testes da interface | Playwright, com o Google Chrome quando ele está instalado |
| Execução | Docker Compose |

O navegador fala só com o frontend, na porta 3000. O Nginx encaminha `/api/` ao serviço `backend` na rede do Compose (`backend:5000`). Por isso a página não precisa do endereço interno do contêiner.

## Comunicação entre frontend e backend

`POST /api/analisar`

Pedido:

```json
{ "codigo": "int numero = 10;\n" }
```

Código tokenizado sem erro léxico (`200`):

```json
{
  "recebido": true,
  "sucesso": true,
  "mensagem": "Análise léxica concluída. 5 tokens reconhecidos. A análise sintática ainda não está disponível nesta versão.",
  "caracteres": 17,
  "tokens": [
    { "tipo": "PALAVRA_RESERVADA", "lexema": "int", "linha": 1, "coluna": 1 },
    { "tipo": "IDENTIFICADOR", "lexema": "numero", "linha": 1, "coluna": 5 },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 12 },
    { "tipo": "LITERAL_INTEIRO", "lexema": "10", "linha": 1, "coluna": 14 },
    { "tipo": "DELIMITADOR", "lexema": ";", "linha": 1, "coluna": 16 }
  ],
  "erros": []
}
```

Erro léxico (`200`, com `sucesso` falso). O HTTP continua 200 porque a requisição foi compreendida; o problema está no programa, não no transporte:

```json
{
  "recebido": true,
  "sucesso": false,
  "mensagem": "A análise léxica encontrou 1 erro léxico. Os trechos válidos foram tokenizados mesmo assim. A análise sintática ainda não está disponível nesta versão.",
  "tokens": [
    { "tipo": "IDENTIFICADOR", "lexema": "a", "linha": 1, "coluna": 1 },
    { "tipo": "IDENTIFICADOR", "lexema": "b", "linha": 1, "coluna": 5 }
  ],
  "erros": [
    {
      "tipo": "ERRO_LEXICO",
      "lexema": "@",
      "linha": 1,
      "coluna": 3,
      "mensagem": "Erro léxico na linha 1, coluna 3: caractere não reconhecido '@'. Verifique se ele faz parte do subconjunto suportado."
    }
  ]
}
```

O exemplo acima corresponde à entrada `a @ b`, que ainda produz os identificadores `a` e `b` em `tokens`.

Entrada vazia ou só com espaços (`400`):

```json
{ "recebido": false, "mensagem": "Informe um código-fonte antes de solicitar a análise." }
```

A frase muda quando o texto existe, mas não tem conteúdo útil: "Não há conteúdo útil para analisar. Informe um programa antes de continuar."

JSON ausente, campo `codigo` ausente ou `codigo` que não é texto (`400`):

```json
{
  "recebido": false,
  "mensagem": "A requisição é inválida. Envie um JSON com o campo \"codigo\" contendo o texto do programa."
}
```

Falha interna (`500`): uma mensagem genérica, sem rastreamento, caminho do servidor ou detalhe da exceção.

Se o frontend não obtém resposta, a tela mostra: "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente."

A rota `GET /api/hello` da primeira etapa continua respondendo `{"message":"Hello, World!"}`. `GET /api/health` é o healthcheck do contêiner.

## Pré-requisitos

- Docker Engine 24 ou superior (neste ambiente: 29.8.2)
- Docker Compose V2 (`docker compose`, com espaço; neste ambiente: v5.5.1)

Para a suíte local, além do Docker:

- Python 3.11 ou superior
- Node.js 22 ou superior
- Google Chrome, para os testes de interface neste Windows

Confira as versões:

```bash
docker --version
docker compose version
```

## Clonagem e inicialização

```bash
git clone https://github.com/luquinhaalho/Compiladores.git
cd Compiladores
docker compose up --build
```

Abra [http://localhost:3000](http://localhost:3000). Escolha um exemplo, edite o código se quiser e clique em **Analisar**.

Para deixar os contêineres em segundo plano:

```bash
docker compose up --build -d
```

A API também responde em [http://localhost:5000/api/analisar](http://localhost:5000/api/analisar). O caminho que passa pela rede entre os contêineres é o da porta 3000.

## Encerramento

No terminal em que o Compose está em primeiro plano, use `Ctrl+C` e depois:

```bash
docker compose down
```

O mesmo comando encerra os serviços iniciados com `-d`.

## Testes

Os registros de execução estão em [docs/testes.md](docs/testes.md).

Backend, na pasta `backend`, com o ambiente virtual já criado:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

No Linux ou no macOS, o executável fica em `.venv/bin/python`. A suíte padrão não sobe o Docker. Ela cobre o scanner, a classificação da entrada, o contrato de `POST /api/analisar`, os exemplos e a rota `GET /api/hello`.

Interface, na pasta `frontend`:

```bash
npm install
npx playwright install chromium
npm test
```

Se o Google Chrome estiver em `C:\Program Files\Google\Chrome\Application\chrome.exe`, o Playwright usa esse navegador e o `npx playwright install chromium` pode ser omitido.

Implantação, com o daemon do Docker em execução, a partir de `backend`:

```bash
.venv\Scripts\python -m pytest -m deploy --override-ini="addopts="
```

Esse teste constrói as imagens, espera o healthcheck, envia um programa pela porta 3000, confere o token `numero`, recusa uma entrada em branco e derruba os contêineres ao final.

## Estrutura do repositório

```text
.
├── backend/
│   ├── app/
│   │   ├── lexer.py
│   │   ├── main.py
│   │   ├── mensagens.py
│   │   └── validacao.py
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── tests/interface.spec.js
│   └── Dockerfile
├── docs/escopo-lexico.md
├── docs/testes.md
├── docker-compose.yml
└── README.md
```

## Limitações desta versão

- Não há analisador sintático nem semântico, e nenhuma AST é desenhada. Tokens válidos em uma ordem inválida são aceitos pelo scanner e serão recusados na etapa do parser.
- Não há cadeias, caracteres entre aspas, operadores compostos (`==`, `<=`, `++`), comandos `if`/`while` nem identificadores com acento.
- Literais reais exigem dígitos dos dois lados do ponto. `007` é um inteiro decimal, não um octal.
- Os testes de interface dependem de Node.js e de um navegador (Chrome instalado ou Chromium do Playwright).
- O teste marcado com `deploy` altera o estado do Docker local e usa as portas 3000 e 5000.
