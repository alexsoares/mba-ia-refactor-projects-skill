const { PaymentStatus, APPROVED_CARD_PREFIX } = require('../constants');

// Gateway simulado. A chave vem da config e nunca é logada, assim como o número do cartão.
class PaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    charge({ card, amount }) {
        const status = card.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
        this.logger.info(`Cobrança de ${amount} no cartão final ${card.slice(-4)}: ${status}`);
        return status;
    }
}

module.exports = PaymentGateway;
