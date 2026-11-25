"""Cliente do Ollama para explicações didáticas.

A IA não substitui o scanner nem o parser: ela só comenta os resultados
já produzidos pelo compilador. Se o serviço estiver indisponível, a
análise léxica e sintática continua funcionando.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

SYSTEM_PROMPT = """Você é um professor especialista em Compiladores e Linguagens Formais.
Sua função é explicar didaticamente os resultados produzidos por um software educacional de compiladores.

O sistema poderá fornecer: código-fonte; tokens; gramática utilizada; AST; erros sintáticos; perguntas do estudante.

Regras obrigatórias:
1. Explique em português brasileiro, com linguagem clara e exemplos simples.
2. Explique passo a passo.
3. Considere a gramática e os resultados fornecidos pelo sistema.
4. Ao explicar a AST, descreva a função dos nós e a relação entre eles.
5. Ao explicar erros sintáticos, indique a regra gramatical relacionada, quando disponível.
6. Não invente tokens, nós ou erros que não estejam nos dados recebidos.
7. Não afirme que o compilador realizou uma análise não apresentada.
8. Se alguma informação estiver ausente, informe essa limitação.
9. Não substitua a análise realizada pelo scanner ou parser.
10. Diferencie claramente os conceitos teóricos dos resultados efetivamente produzidos.

O objetivo é ajudar o estudante a compreender o funcionamento do compilador, e não simplesmente fornecer uma resposta pronta."""

MENSAGEM_IA_INDISPONIVEL = (
    "O assistente de IA não está disponível no momento. "
    "A análise léxica e sintática continua funcionando normalmente. "
    "Verifique se o serviço Ollama está em execução e se o modelo llama3.2 foi baixado."
)
MENSAGEM_IA_TIMEOUT = (
    "O assistente de IA demorou demais para responder. "
    "Tente novamente em instantes; a análise do compilador não foi afetada."
)
MENSAGEM_IA_VAZIA = (
    "O assistente de IA retornou uma resposta vazia. Tente reformular a pergunta."
)


def configuracao() -> dict[str, Any]:
    return {
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip(
            "/"
        ),
        "model": os.environ.get("OLLAMA_MODEL", "llama3.2"),
        "timeout": float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "180")),
    }


def montar_pergunta_usuario(
    tipo: str,
    pergunta: str,
    codigo: str,
    contexto: dict[str, Any] | None,
) -> str:
    partes = [
        f"Tipo de pedido: {tipo}",
        f"Código-fonte:\n{codigo or '(ausente)'}",
        f"Pergunta do estudante:\n{pergunta}",
    ]
    if contexto:
        partes.append(
            "Contexto produzido pelo compilador (JSON):\n"
            + json.dumps(contexto, ensure_ascii=False, indent=2)
        )
    partes.append(
        "Explique com base apenas nesses dados. Não invente tokens, nós ou erros."
    )
    return "\n\n".join(partes)


def explicar(
    tipo: str,
    pergunta: str,
    codigo: str,
    contexto: dict[str, Any] | None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Chama o Ollama e devolve um dicionário com sucesso/mensagem/explicacao."""
    cfg = configuracao()
    payload = {
        "model": cfg["model"],
        "stream": False,
        "options": {
            # Respostas didáticas curtas: evita estourar o proxy do Nginx.
            "num_predict": int(os.environ.get("OLLAMA_NUM_PREDICT", "256")),
            "temperature": 0.4,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": montar_pergunta_usuario(tipo, pergunta, codigo, contexto),
            },
        ],
    }
    url = f"{cfg['base_url']}/api/chat"
    proprio = client is None
    http = client or httpx.Client(timeout=cfg["timeout"])
    try:
        resposta = http.post(url, json=payload)
        if resposta.status_code >= 500:
            return {
                "sucesso": False,
                "mensagem": MENSAGEM_IA_INDISPONIVEL,
                "explicacao": None,
                "modelo": cfg["model"],
            }
        if resposta.status_code >= 400:
            return {
                "sucesso": False,
                "mensagem": MENSAGEM_IA_INDISPONIVEL,
                "explicacao": None,
                "modelo": cfg["model"],
            }
        dados = resposta.json()
        texto = (
            (dados.get("message") or {}).get("content")
            if isinstance(dados, dict)
            else None
        )
        if not isinstance(texto, str) or not texto.strip():
            return {
                "sucesso": False,
                "mensagem": MENSAGEM_IA_VAZIA,
                "explicacao": None,
                "modelo": cfg["model"],
            }
        return {
            "sucesso": True,
            "mensagem": "Explicação gerada por IA (Ollama / Llama 3.2). Trate-a como apoio didático, não como resultado oficial da compilação.",
            "explicacao": texto.strip(),
            "modelo": cfg["model"],
        }
    except httpx.TimeoutException:
        return {
            "sucesso": False,
            "mensagem": MENSAGEM_IA_TIMEOUT,
            "explicacao": None,
            "modelo": cfg["model"],
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return {
            "sucesso": False,
            "mensagem": MENSAGEM_IA_INDISPONIVEL,
            "explicacao": None,
            "modelo": cfg["model"],
        }
    finally:
        if proprio:
            http.close()
