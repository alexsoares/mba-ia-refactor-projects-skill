// Encaminha rejeições de handlers async para o errorHandler.
module.exports = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
