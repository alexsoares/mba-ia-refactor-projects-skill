// Única fonte de configuração da aplicação (lida de variáveis de ambiente).
const config = Object.freeze({
    port: Number(process.env.PORT || 3000),
    dbFilename: process.env.DB_FILENAME || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Valor exigido no header X-Admin-Token. Vazio = rotas administrativas bloqueadas.
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
    cacheMaxEntries: Number(process.env.CACHE_MAX_ENTRIES || 1000),
});

module.exports = config;
