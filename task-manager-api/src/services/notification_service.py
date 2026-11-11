import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Envia e-mails de notificação. Sem SMTP_HOST configurado, apenas registra no log."""

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @classmethod
    def from_settings(cls, settings):
        return cls(settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD)

    @property
    def enabled(self):
        return bool(self.host)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info("E-mail não enviado (SMTP não configurado): %s", subject)
            return False

        message = EmailMessage()
        message["From"] = self.user
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception("Falha ao enviar e-mail para %s", to)
            return False
        logger.info("E-mail enviado para %s", to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
