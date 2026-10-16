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

## Limitações

Ainda não há testes de análise léxica, sintática ou semântica, porque esses analisadores não existem nesta etapa.
