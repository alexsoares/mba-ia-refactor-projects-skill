const AppError = require('../errors/AppError');

function createErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.status).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
        logger.error(`Erro inesperado em ${req.method} ${req.originalUrl}:`, err);
        return res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
