const { PaymentStatus } = require('../constants');

const SCHEMA = `
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
    CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

// Dados de exemplo para desenvolvimento local.
async function initDatabase(db, { passwordHasher }) {
    await db.exec(SCHEMA);
    const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (total > 0) return;

    await db.transaction(async (tx) => {
        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', passwordHasher.hash('123')]);
        await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
            ['Clean Architecture', 997.0, 'Docker', 497.0]);
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', [PaymentStatus.PAID]);
    });
}

module.exports = { initDatabase };
