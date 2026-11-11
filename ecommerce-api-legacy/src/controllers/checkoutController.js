const AppError = require('../errors/AppError');
const { PaymentStatus } = require('../constants');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d+$/;

// Converte o payload público (usr, eml, pwd, c_id, card) em dados nomeados e válidos.
function parseCheckout(body = {}) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = body;
    if (!name || !email || !courseId || !card) throw new AppError(400, 'Bad Request');
    if (!EMAIL_PATTERN.test(String(email)) || !CARD_PATTERN.test(String(card))) throw new AppError(400, 'Bad Request');
    if (!Number.isInteger(Number(courseId)) || Number(courseId) <= 0) throw new AppError(400, 'Bad Request');
    return { name, email, password, courseId: Number(courseId), card: String(card) };
}

class CheckoutController {
    constructor({ db, courses, users, enrollments, auditLogs, paymentGateway, passwordHasher, cache }) {
        this.db = db;
        this.courses = courses;
        this.users = users;
        this.enrollments = enrollments;
        this.auditLogs = auditLogs;
        this.paymentGateway = paymentGateway;
        this.passwordHasher = passwordHasher;
        this.cache = cache;
    }

    async checkout(body) {
        const { name, email, password, courseId, card } = parseCheckout(body);

        const course = await this.courses.findActiveById(courseId);
        if (!course) throw new AppError(404, 'Curso não encontrado');

        const paymentStatus = this.paymentGateway.charge({ card, amount: course.price });
        if (paymentStatus === PaymentStatus.DENIED) throw new AppError(400, 'Pagamento recusado');

        const { userId, enrollmentId } = await this.db.transaction(async (tx) => {
            const existing = await this.users.findByEmail(email, tx);
            const studentId = existing
                ? existing.id
                : await this.users.create({
                    name,
                    email,
                    passwordHash: this.passwordHasher.hash(password || this.passwordHasher.randomPassword()),
                }, tx);
            const newEnrollmentId = await this.enrollments.create({ userId: studentId, courseId }, tx);
            await this.enrollments.addPayment({ enrollmentId: newEnrollmentId, amount: course.price, status: paymentStatus }, tx);
            await this.auditLogs.record(`Checkout curso ${courseId} por ${studentId}`, tx);
            return { userId: studentId, enrollmentId: newEnrollmentId };
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = CheckoutController;
