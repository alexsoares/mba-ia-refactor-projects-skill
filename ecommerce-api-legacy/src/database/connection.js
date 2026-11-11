const sqlite3 = require('sqlite3');

// Wrapper Promise sobre o driver sqlite3. Como há uma única conexão, todas as operações
// passam por uma fila: assim uma transação nunca é intercalada com comandos de outra requisição.
class Database {
    constructor(filename) {
        this.db = new sqlite3.Database(filename);
        this.queue = Promise.resolve();
        // Executor usado dentro de transaction(): acessa o driver sem passar pela fila.
        this.direct = {
            run: (sql, params) => this.rawRun(sql, params),
            get: (sql, params) => this.rawGet(sql, params),
            all: (sql, params) => this.rawAll(sql, params),
        };
    }

    exclusive(work) {
        const result = this.queue.then(work);
        this.queue = result.catch(() => {});
        return result;
    }

    rawRun(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    rawGet(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    rawAll(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    run(sql, params) {
        return this.exclusive(() => this.rawRun(sql, params));
    }

    get(sql, params) {
        return this.exclusive(() => this.rawGet(sql, params));
    }

    all(sql, params) {
        return this.exclusive(() => this.rawAll(sql, params));
    }

    exec(sql) {
        return this.exclusive(() => new Promise((resolve, reject) => {
            this.db.exec(sql, (err) => (err ? reject(err) : resolve()));
        }));
    }

    transaction(work) {
        return this.exclusive(async () => {
            await this.rawRun('BEGIN');
            try {
                const result = await work(this.direct);
                await this.rawRun('COMMIT');
                return result;
            } catch (err) {
                await this.rawRun('ROLLBACK');
                throw err;
            }
        });
    }

    close() {
        return new Promise((resolve, reject) => this.db.close((err) => (err ? reject(err) : resolve())));
    }
}

module.exports = Database;
