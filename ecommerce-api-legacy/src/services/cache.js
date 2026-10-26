// Cache em memória com limite de entradas (descarta a mais antiga). Instanciado no composition root.
class Cache {
    constructor({ maxEntries }) {
        this.maxEntries = maxEntries;
        this.entries = new Map();
    }

    set(key, value) {
        this.entries.delete(key);
        this.entries.set(key, value);
        if (this.entries.size > this.maxEntries) {
            this.entries.delete(this.entries.keys().next().value);
        }
    }

    get(key) {
        return this.entries.get(key);
    }
}

module.exports = Cache;
