from src.constants import DESCONTO_POR_FATURAMENTO


def calcular_desconto(faturamento):
    return next((faturamento * percentual for limite, percentual in DESCONTO_POR_FATURAMENTO
                 if faturamento > limite), 0)


class RelatorioController:
    def __init__(self, pedido_model):
        self.pedidos = pedido_model

    def vendas(self):
        resumo = self.pedidos.resumo_vendas()
        faturamento = resumo["faturamento"]
        total_pedidos = resumo["total_pedidos"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
