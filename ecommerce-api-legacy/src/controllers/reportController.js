const { PaymentStatus } = require('../constants');

class ReportController {
    constructor({ courses }) {
        this.courses = courses;
    }

    async financialReport() {
        const rows = await this.courses.findRevenueRows();
        const report = new Map();

        for (const row of rows) {
            if (!report.has(row.course_id)) {
                report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const courseReport = report.get(row.course_id);
            if (row.status === PaymentStatus.PAID) courseReport.revenue += row.amount;
            courseReport.students.push({
                student: row.student ?? 'Unknown',
                paid: row.amount ?? 0,
            });
        }

        return [...report.values()];
    }
}

module.exports = ReportController;
