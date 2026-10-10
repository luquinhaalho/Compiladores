# Compiladores — visualização de AST

Laboratório educacional para gerar e visualizar árvores de sintaxe abstrata (AST) de um subconjunto didático de Java. Esta primeira etapa entrega o esqueleto da aplicação web, os contêineres e a prova de comunicação entre frontend e backend.

## Linguagem e subconjunto didático

A linguagem-alvo é **Java**.

O recorte desta ferramenta não é a linguagem inteira. O subconjunto didático cobre:

- declaração de variáveis com tipo, nome e inicializador;
- expressões aritméticas com literais, identificadores, parênteses e os operadores `+`, `-`, `*` e `/`.

Gramática inicial, em EBNF:

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

Exemplo aceito por esse recorte:

```java
int total = (a + 2) * 3;
double media = total / 2;
```

Java foi escolhida porque é uma linguagem orientada a objetos com uma sintaxe rica: tipos, declarações, operadores e, nas etapas seguintes, construções como blocos, chamadas e estruturas de controle. Esse vocabulário produz árvores AST com nós de naturezas distintas, o que torna a visualização útil para ensinar a fronteira entre árvore concreta e árvore abstrata. O subconjunto começa pequeno de propósito, para que cada fase do compilador (léxico, sintático, AST) possa ser estudada isoladamente.

## Arquitetura desta etapa

O navegador conversa apenas com o frontend, em `http://localhost:3000`. O Nginx desse contêiner encaminha qualquer caminho `/api/` ao serviço `backend` na rede do Docker Compose (`backend:5000`). A rota de prova é `GET /api/hello`, que responde:

```json
{ "message": "Hello, World!" }
```

| Serviço   | Tecnologia        | Porta no host |
|-----------|-------------------|---------------|
| frontend  | Nginx + HTML/JS   | 3000          |
| backend   | Python + FastAPI  | 5000          |

## Estrutura do repositório

```text
.
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── public/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── docker-compose.yml
└── README.md
```

## Pré-requisitos

- [Docker Engine](https://docs.docker.com/engine/install/) 24 ou superior
- Docker Compose V2, o plugin embutido no Docker (`docker compose`, com espaço)

Confira as versões:

```bash
docker --version
docker compose version
```

O Compose V2 acompanha o Docker Desktop e a maioria das instalações recentes do Engine. Não é necessário instalar Python nem Node na máquina: as dependências ficam dentro das imagens.

## Clonagem e inicialização

```bash
git clone <url-do-repositorio>
cd Compiladores
docker compose up --build
```

O primeiro arranque constrói as duas imagens e sobe os serviços. Quando o frontend estiver saudável, abra [http://localhost:3000](http://localhost:3000). A página deve exibir **Hello, World!**, texto vindo do backend.

Para deixar os contêineres em segundo plano:

```bash
docker compose up --build -d
```

A API também responde direto em [http://localhost:5000/api/hello](http://localhost:5000/api/hello). O caminho que valida a rede entre os contêineres é o da porta 3000: o Nginx do frontend é quem chama o backend.

## Encerramento

No terminal em que o Compose está em primeiro plano, use `Ctrl+C` e depois:

```bash
docker compose down
```

Se os serviços foram iniciados com `-d`, o mesmo comando encerra e remove os contêineres:

```bash
docker compose down
```

## Verificação rápida

Com os serviços no ar:

```bash
curl http://localhost:3000/api/hello
curl http://localhost:5000/api/hello
```

As duas respostas devem ser `{"message":"Hello, World!"}`. A primeira passa pelo contêiner do frontend; a segunda fala direto com o backend.
