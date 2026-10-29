# Registro de testes

Execução da segunda etapa em 16 de outubro de 2026, no Windows do ambiente de desenvolvimento.

## Backend — testes unitários e de endpoint

- Módulo: validação de entrada, `POST /api/analisar`, exemplos e regressão de `GET /api/hello`.
- Tipo: unitário e de endpoint.
- Comando, a partir de `backend`:

```bash
.venv\Scripts\python -m pytest
```

- Resultado: 18 aprovados, 0 reprovados, 1 desmarcado (o teste `deploy`) e 1 aviso. O aviso é o `StarletteDeprecationWarning` do `TestClient`, que recomenda `httpx2`. A suíte terminou em 0,72 s.
- Falhas: nenhuma nesta execução.
- Correção anterior: o tratamento genérico de exceção passou a preservar o 404 de rota inexistente, em vez de convertê-lo em erro interno.

## Interface

- Módulo: tela principal, exemplos, envio do código e mensagens de erro.
- Tipo: teste de interface com Playwright.
- Comando, a partir de `frontend`:

```bash
npx playwright test
```

- Resultado: 6 aprovados, 0 reprovados, em 7,3 s. O Playwright usou o Google Chrome instalado na máquina.
- Falha encontrada antes da correção: a primeira execução não abriu o navegador porque o download do Chromium em `cdn.playwright.dev` expirou. A configuração passou a usar o Chrome local quando ele existe em `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- Pendência: em uma máquina sem esse Chrome, é preciso `npx playwright install chromium` antes de `npm test`.

## Implantação

- Módulo: Docker Compose, healthcheck e `POST /api/analisar` através do Nginx.
- Tipo: teste de implantação.
- Comando, a partir de `backend`:

```bash
.venv\Scripts\python -m pytest -m deploy --override-ini="addopts="
```

- Resultado: 1 aprovado, 18 desmarcados, em 19,40 s. O teste sobe os contêineres, confirma `GET /api/hello` e o envio de código pela porta 3000, recusa entrada só com espaços e executa `docker compose down`.
- Ambiente: Docker Engine 29.8.2 e Compose v5.5.1.

## Scanner — testes unitários e de endpoint

- Módulo: `backend/app/lexer.py` e `POST /api/analisar`.
- Tipo: unitário e de endpoint, incluindo regressão da validação da etapa 2 e de `GET /api/hello`.
- Comando, a partir de `backend`:

```bash
.venv\Scripts\python -m pytest
```

- Resultado em 27 de outubro de 2026: 66 aprovados, 0 reprovados, 1 desmarcado (o teste `deploy`) e 1 aviso. O aviso é o `StarletteDeprecationWarning` do `TestClient`. A suíte terminou em 2,54 s.
- Aspas são agrupadas numa sequência só, para que o texto entre elas não vire identificador.

## Interface com tokens

- Módulo: tabela de tokens, passo a passo, erros léxicos e regressão da etapa 2.
- Tipo: teste de interface com Playwright.
- Comando, a partir de `frontend`:

```bash
npx playwright test
```

- Resultado em 27 de outubro de 2026: 8 aprovados, 0 reprovados, em 7,3 s. O Playwright usou o Google Chrome instalado na máquina.

## Implantação

- Módulo: Docker Compose, healthcheck e tokenização através do Nginx.
- Tipo: teste de implantação.
- Comando, a partir de `backend`:

```bash
.venv\Scripts\python -m pytest -m deploy --override-ini="addopts="
```

- Resultado em 27 de outubro de 2026: 1 reprovado. O Docker CLI respondeu, mas o daemon não estava em execução (`failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`). As imagens não foram reconstruídas nesta tentativa.
- A suíte de backend e a de interface não dependem do daemon e passaram na mesma data.
- Correção pendente: iniciar o Docker Desktop e repetir o comando acima.

## Limitações

Ainda não há testes de análise sintática ou semântica, porque esses analisadores não existem nesta etapa.
