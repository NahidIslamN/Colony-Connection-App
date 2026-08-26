import os
import sys
import django

def main():
    default_settings_module = (
        "config.settings.prod"
        if os.getenv("APP_ENV", "development").strip().lower() in {"prod", "production"}
        else "config.settings.dev"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", default_settings_module))
    django.setup()

    from apps.managements.models import Colony

    print("Checking colonies...")
    total_colonies = Colony.objects.count()
    inactive_colonies = Colony.objects.exclude(status="active")
    inactive_count = inactive_colonies.count()

    print(f"Total colonies: {total_colonies}")
    print(f"Colonies to activate: {inactive_count}")

    if inactive_count > 0:
        updated = inactive_colonies.update(status="active")
        print(f"Successfully activated {updated} colonies!")
    else:
        print("All colonies are already active.")

if __name__ == "__main__":
    main()
