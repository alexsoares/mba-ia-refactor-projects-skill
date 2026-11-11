import logging

from sqlalchemy import delete, func, select

from src.controllers.validators import validate_new_user, validate_user_update
from src.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from src.models import Task, User
from src.utils.time import utcnow

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, session, token_service):
        self.session = session
        self.tokens = token_service

    def _get_or_404(self, user_id):
        user = self.session.get(User, user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def _ensure_email_available(self, email, current_user_id=None):
        existing = self.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing and existing.id != current_user_id:
            raise ConflictError('Email já cadastrado')

    def list(self):
        rows = self.session.execute(
            select(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()
        return [{**user.to_dict(), 'task_count': task_count} for user, task_count in rows]

    def get(self, user_id):
        user = self._get_or_404(user_id)
        tasks = self.session.execute(select(Task).where(Task.user_id == user_id).order_by(Task.id)).scalars()
        return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}

    def create(self, data):
        fields = validate_new_user(data)
        self._ensure_email_available(fields['email'])
        user = User(name=fields['name'], email=fields['email'], role=fields['role'])
        user.set_password(fields['password'])
        self.session.add(user)
        self.session.commit()
        logger.info("Usuário criado: %s", user.id)
        return user.to_dict()

    def update(self, user_id, data):
        user = self._get_or_404(user_id)
        fields = validate_user_update(data)
        if 'email' in fields:
            self._ensure_email_available(fields['email'], current_user_id=user_id)
        password = fields.pop('password', None)
        for name, value in fields.items():
            setattr(user, name, value)
        if password:
            user.set_password(password)
        self.session.commit()
        return user.to_dict()

    def delete(self, user_id):
        user = self._get_or_404(user_id)
        self.session.execute(delete(Task).where(Task.user_id == user_id))
        self.session.delete(user)
        self.session.commit()
        logger.info("Usuário deletado: %s", user_id)

    def tasks(self, user_id):
        self._get_or_404(user_id)
        tasks = self.session.execute(select(Task).where(Task.user_id == user_id).order_by(Task.id)).scalars()
        now = utcnow()
        return [{
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'created_at': str(task.created_at),
            'due_date': str(task.due_date) if task.due_date else None,
            'overdue': task.is_overdue(now),
        } for task in tasks]

    def login(self, data):
        if not data or not isinstance(data, dict):
            raise ValidationError('Dados inválidos')
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        # check_password pode ter migrado um hash legado.
        self.session.commit()

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.tokens.issue(user.id),
        }
