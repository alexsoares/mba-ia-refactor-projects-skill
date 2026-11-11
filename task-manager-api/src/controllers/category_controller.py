from sqlalchemy import func, select, update

from src.controllers.validators import validate_category
from src.errors import NotFoundError
from src.models import Category, Task


class CategoryController:
    def __init__(self, session):
        self.session = session

    def _get_or_404(self, category_id):
        category = self.session.get(Category, category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def list(self):
        rows = self.session.execute(
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
        ).all()
        return [{**category.to_dict(), 'task_count': task_count} for category, task_count in rows]

    def create(self, data):
        category = Category(**validate_category(data, partial=False))
        self.session.add(category)
        self.session.commit()
        return category.to_dict()

    def update(self, category_id, data):
        category = self._get_or_404(category_id)
        for name, value in validate_category(data, partial=True).items():
            setattr(category, name, value)
        self.session.commit()
        return category.to_dict()

    def delete(self, category_id):
        category = self._get_or_404(category_id)
        # Desassocia as tasks na mesma transação para não deixar FKs órfãs.
        self.session.execute(update(Task).where(Task.category_id == category_id).values(category_id=None))
        self.session.delete(category)
        self.session.commit()
