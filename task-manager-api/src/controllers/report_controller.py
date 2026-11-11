from datetime import timedelta

from sqlalchemy import case, func, select

from src.constants import HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from src.controllers.task_controller import overdue_filter
from src.errors import NotFoundError
from src.models import Category, Task, User
from src.utils.time import utcnow


def completion_rate(completed, total):
    return round((completed / total) * 100, 2) if total > 0 else 0


class ReportController:
    def __init__(self, session):
        self.session = session

    def _count(self, model, *conditions):
        return self.session.scalar(select(func.count()).select_from(model).where(*conditions))

    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        by_status = dict(self.session.execute(select(Task.status, func.count()).group_by(Task.status)).all())
        by_priority = dict(self.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all())
        overdue_tasks = self.session.execute(
            select(Task).where(overdue_filter(now)).order_by(Task.id)
        ).scalars().all()
        productivity = self.session.execute(
            select(User.id, User.name, func.count(Task.id),
                   func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self._count(Task),
                'total_users': self._count(User),
                'total_categories': self._count(Category),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [{
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                } for task in overdue_tasks],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._count(Task, Task.created_at >= since),
                'tasks_completed_last_7_days': self._count(Task, Task.status == 'done', Task.updated_at >= since),
            },
            'user_productivity': [{
                'user_id': user_id,
                'user_name': user_name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            } for user_id, user_name, total, completed in productivity],
        }

    def user_report(self, user_id):
        user = self.session.get(User, user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self.session.execute(select(Task).where(Task.user_id == user_id)).scalars().all()
        now = utcnow()
        counts = {status: sum(1 for task in tasks if task.status == status) for status in TASK_STATUSES}
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': len(tasks),
                **counts,
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': completion_rate(counts['done'], len(tasks)),
            },
        }
