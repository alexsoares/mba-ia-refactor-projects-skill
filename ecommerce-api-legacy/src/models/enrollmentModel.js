class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }, executor = this.db) {
        const { lastID } = await executor.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]);
        return lastID;
    }

    async addPayment({ enrollmentId, amount, status }, executor = this.db) {
        const { lastID } = await executor.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]);
        return lastID;
    }
}

module.exports = EnrollmentModel;
