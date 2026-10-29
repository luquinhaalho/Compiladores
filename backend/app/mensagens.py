"""Textos do contrato entre a interface e a API.

As mesmas frases de validação são usadas pelo frontend. Se uma delas mudar,
os testes e o README precisam acompanhar a alteração.
"""

MENSAGEM_VAZIA = "Informe um código-fonte antes de solicitar a análise."
MENSAGEM_BRANCO = (
    "Não há conteúdo útil para analisar. Informe um programa antes de continuar."
)
MENSAGEM_REQUISICAO_INVALIDA = (
    'A requisição é inválida. Envie um JSON com o campo "codigo" contendo o texto do programa.'
)
MENSAGEM_RECEBIDO = "O código possui conteúdo e pode seguir para a análise léxica."
MENSAGEM_INESPERADA = (
    "Ocorreu um erro inesperado ao processar o código. Tente novamente."
)
