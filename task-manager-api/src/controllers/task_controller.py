import logging

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from src.constants import CLOSED_STATUSES, TASK_STATUSES
from src.controllers.validators import parse_int_param, validate_task
from src.errors import NotFoundError
from src.models import Category, Task, User
from src.utils.time import utcnow

logger = logging.getLogger(__name__)


def overdue_filter(now):
    """Condição SQL equivalente a Task.is_overdue()."""
    return (Task.due_date.is_not(None)) & (Task.due_date < now) & (Task.status.not_in(CLOSED_STATUSES))


class TaskController:
    def __init__(self, session, notifications):
        self.session = session
        self.notifications = notifications

    def _get_or_404(self, task_id):
        task = self.session.get(Task, task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _ensure_references(self, fields):
        if fields.get('user_id') and not self.session.get(User, fields['user_id']):
            raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and not self.session.get(Category, fields['category_id']):
            raise NotFoundError('Categoria não encontrada')

    def list(self):
        tasks = self.session.execute(
            select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        ).scalars().all()
        now = utcnow()
        return [{
            **task.to_dict(),
            'overdue': task.is_overdue(now),
            'user_name': task.user.name if task.user else None,
            'category_name': task.category.name if task.category else None,
        } for task in tasks]

    def get(self, task_id):
        task = self._get_or_404(task_id)
        return {**task.to_dict(), 'overdue': task.is_overdue()}

    def create(self, data):
        fields = validate_task(data, partial=False)
        self._ensure_references(fields)
        task = Task(**fields)
        self.session.add(task)
        self.session.commit()
        logger.info("Task criada: %s", task.id)
        self._notify_assignment(task)
        return task.to_dict()

    def update(self, task_id, data):
        task = self._get_or_404(task_id)
        fields = validate_task(data, partial=True)
        self._ensure_references(fields)
        previous_user_id = task.user_id
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow()
        self.session.commit()
        logger.info("Task atualizada: %s", task.id)
        if task.user_id != previous_user_id:
            self._notify_assignment(task)
        return task.to_dict()

    def delete(self, task_id):
        task = self._get_or_404(task_id)
        self.session.delete(task)
        self.session.commit()
        logger.info("Task deletada: %s", task_id)

    def search(self, query, status, priority, user_id):
        stmt = select(Task).order_by(Task.id)
        if query:
            stmt = stmt.where(or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
        if status:
            stmt = stmt.where(Task.status == status)
        priority = parse_int_param(priority, 'priority')
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        user_id = parse_int_param(user_id, 'user_id')
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return [task.to_dict() for task in self.session.execute(stmt).scalars()]

    def stats(self):
        by_status = dict(self.session.execute(select(Task.status, func.count()).group_by(Task.status)).all())
        total = sum(by_status.values())
        overdue = self.session.scalar(select(func.count()).select_from(Task).where(overdue_filter(utcnow())))
        done = by_status.get('done', 0)
        return {
            'total': total,
            **{status: by_status.get(status, 0) for status in TASK_STATUSES},
            'overdue': overdue,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }

    def _notify_assignment(self, task):
        if task.user_id:
            self.notifications.notify_task_assigned(task.user, task)
