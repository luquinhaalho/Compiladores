# Compiladores — visualização de AST

Software educacional para experimentar, em etapas, a geração e a visualização de árvores de sintaxe abstrata (AST). Nesta versão o estudante escreve ou escolhe um programa, pede o processamento e vê a resposta da aplicação. A análise léxica, sintática e semântica ainda não é feita.

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

## O que a interface faz

A tela em [http://localhost:3000](http://localhost:3000) identifica o laboratório e a linguagem Java. Ela oferece:

- um campo monoespaçado para escrever, colar e editar o código-fonte;
- uma lista com três exemplos, que substituem o texto do campo e podem ser editados depois;
- o botão **Analisar**, que envia o código ao backend;
- uma área de resultado com a mensagem da validação ou da falha de comunicação.

O código permanece no campo depois do envio. Entradas com erro proposital são aceitas quando têm algum texto: o parser ainda não existe.

### Exemplos disponíveis

| Exemplo | Código | Construção demonstrada |
|---|---|---|
| Declaração e inicialização | `int numero = 10;` | Variável `int` com literal inteiro |
| Expressão aritmética | `int resultado = (10 + 5) * 2;` | Soma, multiplicação e parênteses |
| Duas declarações | `int total = 8;` e `double media = total / 2;` | Dois tipos e uma divisão |

Os textos ficam em `frontend/public/examples.json`. Estruturas condicionais ficam de fora porque ainda não pertencem ao subconjunto.

## Tecnologias

| Parte | Tecnologia |
|---|---|
| Frontend | HTML, CSS e JavaScript, servidos por Nginx |
| Backend | Python 3.12 e FastAPI |
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

Código recebido (`200`):

```json
{
  "recebido": true,
  "mensagem": "Código recebido com sucesso. A análise léxica, sintática e semântica ainda não está disponível nesta versão.",
  "caracteres": 18
}
```

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

No Linux ou no macOS, o executável fica em `.venv/bin/python`. A suíte padrão não sobe o Docker. Ela cobre a classificação da entrada, o contrato de `POST /api/analisar`, os exemplos e a rota `GET /api/hello`.

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

Esse teste constrói as imagens, espera o healthcheck, envia um programa e uma entrada em branco pela porta 3000 e derruba os contêineres ao final.

## Estrutura do repositório

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── mensagens.py
│   │   └── validacao.py
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── tests/interface.spec.js
│   └── Dockerfile
├── docs/testes.md
├── docker-compose.yml
└── README.md
```

## Limitações desta versão

- Não há analisador léxico, sintático nem semântico, e nenhuma AST é desenhada.
- Qualquer texto que não seja vazio nem só espaços é aceito, inclusive código fora do subconjunto.
- Os testes de interface dependem de Node.js e de um navegador (Chrome instalado ou Chromium do Playwright).
- O teste marcado com `deploy` altera o estado do Docker local e usa as portas 3000 e 5000.
