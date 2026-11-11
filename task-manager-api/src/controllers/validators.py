"""Validação de entrada centralizada (mensagens preservadas do contrato original)."""
import re
from datetime import datetime

from src.constants import (
    COLOR_PATTERN,
    DATE_FORMAT,
    EMAIL_PATTERN,
    MIN_PASSWORD_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_ROLES,
)
from src.errors import ValidationError


def require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def _validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _parse_due_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')


def _normalize_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def validate_task(data, partial):
    """Valida o payload de task. Em `partial` (update), só os campos enviados são validados."""
    data = require_payload(data)
    fields = {}

    if not partial and not data.get('title'):
        raise ValidationError('Título é obrigatório')
    if 'title' in data:
        fields['title'] = _validate_title(data['title'])
    if 'description' in data or not partial:
        fields['description'] = data.get('description', '')
    if 'status' in data or not partial:
        status = data.get('status', 'pending')
        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        fields['status'] = status
    if 'priority' in data:
        fields['priority'] = _validate_priority(data['priority'])
    for ref in ('user_id', 'category_id'):
        if ref in data:
            fields[ref] = data[ref] or None
    if 'due_date' in data:
        fields['due_date'] = _parse_due_date(data['due_date'])
    if 'tags' in data:
        fields['tags'] = _normalize_tags(data['tags']) or None
    return fields


def validate_email(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def validate_new_user(data):
    data = require_payload(data)
    for field, message in (('name', 'Nome é obrigatório'),
                           ('email', 'Email é obrigatório'),
                           ('password', 'Senha é obrigatória')):
        if not data.get(field):
            raise ValidationError(message)
    validate_email(data['email'])
    if len(data['password']) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    role = data.get('role', 'user')
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return {'name': data['name'], 'email': data['email'], 'password': data['password'], 'role': role}


def validate_user_update(data):
    data = require_payload(data)
    fields = {}
    if 'name' in data:
        if not data['name']:
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        fields['email'] = validate_email(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        fields['role'] = data['role']
    if 'active' in data:
        fields['active'] = bool(data['active'])
    return fields


def validate_color(color):
    if not isinstance(color, str) or not re.match(COLOR_PATTERN, color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def validate_category(data, partial):
    data = require_payload(data)
    fields = {}
    if not partial and not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    if 'name' in data:
        if not data['name']:
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'description' in data or not partial:
        fields['description'] = data.get('description', '')
    if 'color' in data:
        fields['color'] = validate_color(data['color'])
    return fields


def parse_int_param(value, name):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')
