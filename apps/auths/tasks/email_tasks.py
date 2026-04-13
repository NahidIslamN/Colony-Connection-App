from celery import shared_task
from django.core.mail import send_mail


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def send_email_to(self, email, text, subject):
    send_mail(subject, text, "from@example.com", [email])
    return "Email sent successfully."
