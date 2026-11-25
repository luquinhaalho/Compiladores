# Compiladores — visualização de AST

Software educacional para experimentar, em etapas, a geração e a visualização de árvores de sintaxe abstrata (AST). Nesta versão o estudante escreve ou escolhe um programa em um subconjunto de Java, vê os **tokens** do scanner e a **AST** do parser. A análise semântica ainda não é feita.

## Linguagem e subconjunto didático

A linguagem analisada é **Java**.

O recorte cobre declaração de variáveis com inicializador e expressões aritméticas. A gramática formal, a precedência e o que fica fora do escopo estão em [docs/gramatica.md](docs/gramatica.md). O vocabulário do scanner está em [docs/escopo-lexico.md](docs/escopo-lexico.md). O fluxo completo está em [docs/fluxograma.md](docs/fluxograma.md).

| Categoria léxica | Exemplos |
|---|---|
| Palavras reservadas | `int`, `double`, `boolean`, `true`, `false` |
| Identificadores | `numero`, `resultado`, `_x1` |
| Literais | `10`, `0`, `2.5` |
| Operadores | `+`, `-`, `*`, `/`, `=` |
| Delimitadores | `(`, `)`, `;` |
| Comentários (ignorados) | `// linha` e `/* bloco */` |

## Scanner e parser

| Fase | Arquivo | Estratégia |
|---|---|---|
| Léxica | `backend/app/lexer.py` | Laço caractere a caractere, sem gerador |
| Sintática | `backend/app/parser.py` | Descendente recursivo manual |
| AST | `backend/app/ast_nodes.py` | Nós tipados serializados em JSON |

O parser foi escrito à mão porque o subconjunto é pequeno e cada não terminal vira uma função legível para o estudante. Não há ANTLR, Lark nem Bison.

**Decisão sobre erros léxicos:** se o scanner reportar qualquer erro, o parser **não é executado**. Tokens inválidos gerariam diagnósticos sintáticos sem sentido. Os erros léxicos continuam na resposta e na interface.

**Recuperação sintática:** apenas o **primeiro** erro sintático é reportado. A mensagem inclui o encontrado, o esperado, a localização e a regra EBNF violada.

## O que a interface faz

Em [http://localhost:3000](http://localhost:3000):

- editor monoespaçado e exemplos selecionáveis;
- botão **Analisar** (scanner + parser);
- tabela de tokens, destaque colorido e passo a passo léxico;
- árvore AST navegável, visão textual, expandir/recolher e exportar JSON;
- ao clicar em um nó, o trecho correspondente é destacado no código e a regra gramatical aparece;
- erros léxicos e sintáticos em seções distintas.

### Exemplos disponíveis

| Exemplo | Demonstra |
|---|---|
| Declaração e inicialização | `int numero = 10;` |
| Expressão aritmética | parênteses e operadores |
| Duas declarações | `int` / `double` e literal real |
| Comentário e boolean | comentário ignorado e `true` |
| Precedência `*` sobre `+` | AST com multiplicação sob a adição |
| Erro léxico proposital | `@` — parser não roda |
| Erro sintático proposital | falta `;` — tokens ok, AST nula |

## Tecnologias

| Parte | Tecnologia |
|---|---|
| Frontend | HTML, CSS e JavaScript (Nginx) |
| Backend | Python 3.12, FastAPI, scanner e parser manuais |
| Assistente | Ollama + Llama 3.2 (explicações didáticas) |
| Testes | pytest e Playwright |
| Execução | Docker Compose |

## Comunicação `POST /api/analisar`

Pedido:

```json
{ "codigo": "int resultado = 10 + 5 * 2;\n" }
```

Programa válido (`200`). Os campos `sucesso`, `tokens` e `erros` da Etapa 3 continuam representando o **léxico**:

```json
{
  "recebido": true,
  "sucesso": true,
  "mensagem": "Análise léxica concluída. … Análise sintática concluída. …",
  "caracteres": 30,
  "tokens": [ { "tipo": "PALAVRA_RESERVADA", "lexema": "int", "linha": 1, "coluna": 1 } ],
  "erros": [],
  "lexico": { "sucesso": true, "tokens": [], "erros": [] },
  "sintatico": {
    "executado": true,
    "sucesso": true,
    "ast": {
      "tipo": "PROGRAMA",
      "linha": 1,
      "coluna": 1,
      "linhaFim": 1,
      "colunaFim": 29,
      "atributos": {},
      "regra": "programa = { statement } ;",
      "filhos": [
        {
          "tipo": "DECLARACAO_VARIAVEL",
          "atributos": { "tipoDado": "int", "nome": "resultado" },
          "filhos": [
            {
              "tipo": "ADICAO",
              "atributos": { "operador": "+" },
              "filhos": [
                { "tipo": "LITERAL_INTEIRO", "atributos": { "valor": "10" }, "filhos": [] },
                {
                  "tipo": "MULTIPLICACAO",
                  "atributos": { "operador": "*" },
                  "filhos": [
                    { "tipo": "LITERAL_INTEIRO", "atributos": { "valor": "5" }, "filhos": [] },
                    { "tipo": "LITERAL_INTEIRO", "atributos": { "valor": "2" }, "filhos": [] }
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    "erros": []
  }
}
```

Erro léxico (`sucesso` falso no léxico; `sintatico.executado` falso):

```json
{
  "sucesso": false,
  "erros": [ { "tipo": "ERRO_LEXICO", "lexema": "@", "mensagem": "…" } ],
  "sintatico": { "executado": false, "sucesso": null, "ast": null, "erros": [] }
}
```

Erro sintático (léxico ok; AST nula):

```json
{
  "sucesso": true,
  "sintatico": {
    "executado": true,
    "sucesso": false,
    "ast": null,
    "erros": [
      {
        "tipo": "ERRO_SINTATICO",
        "linha": 1,
        "coluna": 16,
        "encontrado": "fim do código",
        "esperado": [";"],
        "mensagem": "Erro sintático: … Regra: varDecl = …",
        "regra": "varDecl = tipo IDENTIFICADOR \"=\" expressao \";\" ;"
      }
    ]
  }
}
```

`GET /api/hello` e `GET /api/health` permanecem.

## Pré-requisitos

- Docker Engine 24+ e Compose V2
- Para testes locais: Python 3.11+, Node.js 22+, Chrome (ou Chromium do Playwright)

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

Abra [http://localhost:3000](http://localhost:3000). Escolha o exemplo de precedência, clique em **Analisar**, abra o nó `MULTIPLICACAO` e confira a regra na área de status.

```bash
docker compose down
```

## Testes

Registros em [docs/testes.md](docs/testes.md).

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

Interface:

```bash
cd frontend
npm install
npm test
```

Implantação (requer daemon Docker):

```bash
cd backend
.venv\Scripts\python -m pytest -m deploy --override-ini="addopts="
```

## Assistente de IA (Ollama / Llama 3.2)

O Ollama roda como serviço no Docker Compose e o backend fala com ele em `http://ollama:11434`. O navegador **não** acessa o Ollama diretamente.

| Variável | Padrão | Função |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | endereço interno do serviço |
| `OLLAMA_MODEL` | `llama3.2` | modelo usado no `/api/chat` |
| `OLLAMA_TIMEOUT_SECONDS` | `180` | tempo máximo da requisição |
| `OLLAMA_NUM_PREDICT` | `256` | limite de tokens na resposta |

### Subir e baixar o modelo

```bash
docker compose up --build -d
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
```

O volume `ollama_data` preserva o modelo entre recriações do contêiner. A análise léxica/sintática **não** depende do Ollama: se ele estiver offline, o compilador continua funcionando e a interface mostra uma mensagem didática.

### Endpoint `POST /api/ia/explicar`

```json
{
  "tipo": "AST",
  "pergunta": "Por que a multiplicação aparece abaixo da adição?",
  "codigo": "int resultado = 10 + 5 * 2;",
  "contexto": {
    "no": { "tipo": "MULTIPLICACAO", "atributos": { "operador": "*" } },
    "ast": { "tipo": "PROGRAMA", "filhos": [] }
  }
}
```

Resposta de sucesso:

```json
{
  "sucesso": true,
  "mensagem": "Explicação gerada por IA (Ollama / Llama 3.2). …",
  "explicacao": "…texto do modelo…",
  "modelo": "llama3.2"
}
```

### Funcionalidades na interface

- **Explicar** na tabela de tokens;
- **Explicar token atual** (passo a passo léxico);
- **Explicar nó com IA** (nó selecionado na AST);
- **Entender erro sintático com IA**;
- caixa de pergunta livre ao professor virtual.

A IA recebe o código e o contexto real do compilador. Ela não inventa a análise: o system prompt exige basear-se apenas nos dados enviados.

## Estrutura

```text
.
├── backend/app/
│   ├── lexer.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── ollama_client.py
│   ├── main.py
│   ├── mensagens.py
│   └── validacao.py
├── frontend/public/
├── docs/
│   ├── escopo-lexico.md
│   ├── gramatica.md
│   ├── fluxograma.md
│   └── testes.md
├── docker-compose.yml
└── README.md
```

## Limitações desta versão

- Não há análise semântica (tipos, variável não declarada).
- Não há `if`/`while`, chaves, operadores relacionais nem cadeias.
- Só o primeiro erro sintático é reportado.
- A árvore exibida é a AST, não a árvore de derivação concreta.
- O Llama 3.2 pode errar conceitualmente: a explicação é apoio, não resultado oficial.
- Baixar o modelo exige rede e espaço em disco; o primeiro `ollama pull` pode demorar.

## Relação com a Etapa 5

A AST desta etapa será a entrada da análise semântica: tabela de símbolos e verificação de tipos sobre os mesmos nós (`DECLARACAO_VARIAVEL`, expressões, literais).
