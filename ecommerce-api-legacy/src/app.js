// Composition root: monta banco, models, serviços, controllers e rotas.
const express = require('express');

const Database = require('./database/connection');
const { initDatabase } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const AuditLogModel = require('./models/auditLogModel');
const PaymentGateway = require('./services/paymentGateway');
const passwordHasher = require('./services/passwordHasher');
const Cache = require('./services/cache');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const checkoutRoutes = require('./views/checkoutRoutes');
const adminRoutes = require('./views/adminRoutes');
const userRoutes = require('./views/userRoutes');
const requireAdmin = require('./middlewares/requireAdmin');
const { createErrorHandler } = require('./middlewares/errorHandler');

async function createApp({ config, logger }) {
    const db = new Database(config.dbFilename);
    await initDatabase(db, { passwordHasher });

    const users = new UserModel(db);
    const courses = new CourseModel(db);

    const checkoutController = new CheckoutController({
        db,
        courses,
        users,
        enrollments: new EnrollmentModel(db),
        auditLogs: new AuditLogModel(db),
        paymentGateway: new PaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
        passwordHasher,
        cache: new Cache({ maxEntries: config.cacheMaxEntries }),
    });
    const reportController = new ReportController({ courses });
    const userController = new UserController({ users, logger });

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas bloqueadas.');
    const adminOnly = requireAdmin(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use('/api', checkoutRoutes(checkoutController));
    app.use('/api', adminRoutes(reportController, adminOnly));
    app.use('/api', userRoutes(userController, adminOnly));
    app.use(createErrorHandler(logger));

    return { app, db };
}

module.exports = { createApp };
