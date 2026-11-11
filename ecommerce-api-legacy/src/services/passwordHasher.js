const crypto = require('node:crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;

// Hash adaptativo com salt (scrypt, da stdlib) no formato "salt:hash".
const passwordHasher = {
    hash(password) {
        const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
        const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
        return `${salt}:${hash}`;
    },

    verify(password, stored) {
        const [salt, hash] = String(stored).split(':');
        if (!salt || !hash) return false;
        const expected = Buffer.from(hash, 'hex');
        const actual = crypto.scryptSync(password, salt, KEY_LENGTH);
        return expected.length === actual.length && crypto.timingSafeEqual(expected, actual);
    },

    // Usado quando o checkout não informa senha: o usuário precisará redefini-la.
    randomPassword() {
        return crypto.randomBytes(24).toString('base64url');
    },
};

module.exports = passwordHasher;
