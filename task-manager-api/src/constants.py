"""Constantes de domínio (regras de negócio nomeadas)."""

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = ("done", "cancelled")
DEFAULT_STATUS = "pending"

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta" nos relatórios
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DATE_FORMAT = "%Y-%m-%d"

VALID_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"

DEFAULT_COLOR = "#000000"
COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"

RECENT_ACTIVITY_DAYS = 7
