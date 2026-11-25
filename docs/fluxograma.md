# Fluxograma do processo de análise

```text
Estudante
   │
   ▼
Interface web (código-fonte + exemplos)
   │
   ▼
POST /api/analisar  ──►  Validação de entrada
                              │
                    vazia/inválida ──► mensagem 400
                              │
                              ▼
                         Scanner (léxico)
                              │
              ┌───────────────┴───────────────┐
              │ erros léxicos                 │ sucesso
              ▼                               ▼
     tokens + erros                   Parser (sintático)
     parser NÃO executado                     │
                                      ┌───────┴───────┐
                                      │ erro          │ sucesso
                                      ▼               ▼
                               diagnóstico      AST (JSON)
                                      │               │
                                      └───────┬───────┘
                                              ▼
                                   Resposta ao frontend
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                         Tabela tokens   Árvore AST    Erros (léx./sint.)
```

A análise semântica (tabela de símbolos, tipos) ainda não está implementada e será a Etapa 5.
