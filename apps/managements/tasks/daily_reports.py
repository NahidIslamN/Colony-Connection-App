from collections import defaultdict
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from apps.managements.models import Company, CustomerMechanary


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_daily_mechanary_reports(self):
    """
    Sends a daily report to company owners containing all CustomerMechanary notes
    created on the current day, categorized by the assigned sales representative.
    """
    today = timezone.localdate()

    companies = Company.objects.all()

    for company in companies:
        owner_email = company.email
        if not owner_email:
            # Fallback to the associated user's email if company.email is empty
            owner_email = company.user.email if company.user.email else None
            
        if not owner_email:
            continue

        # Get all mechanary notes for the company's customers for today
        mechanaries = CustomerMechanary.objects.filter(
            customer__owner_company=company,
            date=today
        ).select_related("customer").prefetch_related("customer__sales_reps")

        if not mechanaries.exists():
            continue

        notes_by_rep = defaultdict(list)
        unassigned_notes = []

        for mech in mechanaries:
            reps = mech.customer.sales_reps.all()
            if reps.exists():
                for rep in reps:
                    notes_by_rep[rep.full_name].append(mech)
            else:
                unassigned_notes.append(mech)

        report_lines = [
            f"Daily Customer Mechanary Report - {company.company_name}",
            f"Date: {today}",
            "================================================================",
            ""
        ]

        # Add notes grouped by sales rep
        for rep_name, mechs in notes_by_rep.items():
            report_lines.append(f"Sales Representative: {rep_name}")
            report_lines.append("-" * 40)
            for mech in mechs:
                report_lines.append(f"Customer: {mech.customer.company_name} (Owner: {mech.customer.owner_name})")
                report_lines.append(f"Machine Type: {mech.type}")
                report_lines.append(f"Brand/Model: {mech.brand} / {mech.model}")
                report_lines.append(f"Serial Number: {mech.serial_number}")
                report_lines.append(f"Purchase Year: {mech.purchase_year}")
                report_lines.append(f"Condition: {mech.condition}")
                report_lines.append(f"Next Service: {mech.next_nervice}")
                report_lines.append(f"Note: {mech.note}")
                report_lines.append("")
            report_lines.append("")

        # Add unassigned notes if any
        if unassigned_notes:
            report_lines.append("Unassigned Customers (No Sales Rep)")
            report_lines.append("-" * 40)
            for mech in unassigned_notes:
                report_lines.append(f"Customer: {mech.customer.company_name} (Owner: {mech.customer.owner_name})")
                report_lines.append(f"Machine Type: {mech.type}")
                report_lines.append(f"Brand/Model: {mech.brand} / {mech.model}")
                report_lines.append(f"Serial Number: {mech.serial_number}")
                report_lines.append(f"Purchase Year: {mech.purchase_year}")
                report_lines.append(f"Condition: {mech.condition}")
                report_lines.append(f"Next Service: {mech.next_nervice}")
                report_lines.append(f"Note: {mech.note}")
                report_lines.append("")
            report_lines.append("")

        email_body = "\n".join(report_lines)
        subject = f"Daily Mechanary Report - {today}"
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@colonyconnections.com')
        
        send_mail(
            subject=subject,
            message=email_body,
            from_email=from_email,
            recipient_list=[owner_email],
            fail_silently=True,
        )

    return "Daily mechanary reports processed."
