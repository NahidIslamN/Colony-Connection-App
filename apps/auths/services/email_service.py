from apps.auths.tasks.email_tasks import send_email_to


def send_verification_email(email: str, full_name: str, otp: str) -> None:
    subject = "Account Verification - Mealz"
    message = f"""

Hello {full_name},

Thank you for registering with Mealz.

Your One-Time Password (OTP) to verify your account is: {otp}

Please do not share this OTP with anyone. It is valid for a limited time only.

If you did not request this, please ignore this email.


Best regards,
The Mealz Team
"""
    send_email_to.delay(email=email, text=message, subject=subject)
