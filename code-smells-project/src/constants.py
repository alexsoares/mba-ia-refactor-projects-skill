"""Constantes de domínio (regras de negócio nomeadas)."""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

TIPO_USUARIO_PADRAO = "cliente"

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]

# Faixas de desconto do relatório de vendas: (faturamento acima de, percentual), da maior para a menor.
DESCONTO_POR_FATURAMENTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
