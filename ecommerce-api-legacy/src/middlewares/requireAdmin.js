const crypto = require('node:crypto');
const AppError = require('../errors/AppError');

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, a rota fica bloqueada.
function requireAdmin(adminToken) {
    const expected = Buffer.from(adminToken);
    return (req, res, next) => {
        const received = Buffer.from(req.get('X-Admin-Token') || '');
        const valid = expected.length > 0
            && received.length === expected.length
            && crypto.timingSafeEqual(received, expected);
        return valid ? next() : next(new AppError(403, 'Acesso negado'));
    };
}

module.exports = requireAdmin;
