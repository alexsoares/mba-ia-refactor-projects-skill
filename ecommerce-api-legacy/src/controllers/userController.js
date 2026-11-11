const AppError = require('../errors/AppError');

class UserController {
    constructor({ users, logger }) {
        this.users = users;
        this.logger = logger;
    }

    async remove(id) {
        const userId = Number(id);
        if (!Number.isInteger(userId) || userId <= 0) throw new AppError(400, 'Bad Request');

        const deleted = await this.users.deleteWithEnrollments(userId);
        if (!deleted) throw new AppError(404, 'Usuário não encontrado');
        this.logger.info(`Usuário ${userId} removido com matrículas e pagamentos`);
        return 'Usuário deletado, junto com suas matrículas e pagamentos.';
    }
}

module.exports = UserController;
