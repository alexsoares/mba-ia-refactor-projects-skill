// Entry point: npm start
const config = require('./config');
const { createLogger } = require('./config/logger');
const { createApp } = require('./app');

const logger = createLogger(config.logLevel);

createApp({ config, logger })
    .then(({ app }) => {
        app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`))
            .on('error', (err) => {
                logger.error(`Não foi possível escutar na porta ${config.port}: ${err.message}`);
                process.exit(1);
            });
    })
    .catch((err) => {
        logger.error('Falha ao iniciar a aplicação:', err);
        process.exit(1);
    });
