import keyword
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.startapp import Command as DjangoStartAppCommand

APP_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SEGMENT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class Command(DjangoStartAppCommand):
    help = (
        "Creates a project-standard app under apps/ with layered structure. "
        "If a directory is provided, falls back to Django's default startapp behavior."
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--api-prefix",
            type=str,
            default=None,
            help="URL path segment in config/urls.py (default: normalized app name).",
        )
        parser.add_argument(
            "--with-realtime",
            action="store_true",
            help="Create websocket stubs (consumers.py and routing.py).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow existing app directory; only missing files are created.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview actions without writing files.",
        )

    def handle(self, **options):
        target = options.get("directory")
        if target:
            return super().handle(**options)

        raw_name = (options.get("name") or "").strip()
        app_name = self._to_snake_case(raw_name)
        if app_name != raw_name:
            self.stdout.write(
                self.style.WARNING(f'Normalized app name "{raw_name}" -> "{app_name}" for safe module naming.')
            )

        api_prefix = (options.get("api_prefix") or app_name).strip().strip("/")
        with_realtime = options["with_realtime"]
        force = options["force"]
        dry_run = options["dry_run"]

        self._validate_app_name(app_name)
        self._validate_api_prefix(api_prefix)

        base_dir = Path(settings.BASE_DIR).resolve()
        apps_root = (base_dir / "apps").resolve()
        app_dir = (apps_root / app_name).resolve()

        if apps_root not in app_dir.parents:
            raise CommandError("Refusing to write outside apps/ directory.")
        if not apps_root.exists():
            raise CommandError(f"apps/ directory not found at: {apps_root}")
        if app_dir.exists() and not force:
            raise CommandError(f"App directory already exists: {app_dir}. Use --force to fill missing files safely.")

        class_name = self._build_class_name(app_name)
        files_to_create = self._build_file_map(app_name, class_name, with_realtime)

        created_files = []
        skipped_files = []

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run mode: no files will be written."))
        else:
            app_dir.mkdir(parents=True, exist_ok=True)

        for relative_path, content in files_to_create.items():
            target_path = app_dir / relative_path
            if target_path.exists():
                skipped_files.append(target_path)
                continue
            if dry_run:
                created_files.append(target_path)
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            created_files.append(target_path)

        settings_path = base_dir / "config" / "settings" / "base.py"
        urls_path = base_dir / "config" / "urls.py"

        app_config = f"apps.{app_name}.apps.{class_name}Config"
        settings_changed = self._ensure_list_entry(
            file_path=settings_path,
            list_name="INSTALLED_APPS",
            canonical_entry=app_config,
            entry_line=f'    "{app_config}",',
            dry_run=dry_run,
        )
        urls_changed = self._ensure_list_entry(
            file_path=urls_path,
            list_name="urlpatterns",
            canonical_entry=f'include("apps.{app_name}.urls")',
            entry_line=f'    path("api/v1/{api_prefix}/", include("apps.{app_name}.urls")),',
            dry_run=dry_run,
        )

        self.stdout.write(self.style.SUCCESS(f"Scaffold prepared for app: {app_name}"))
        self.stdout.write(f"App dir: {app_dir}")
        self.stdout.write(f"API path: /api/v1/{api_prefix}/")
        self.stdout.write(f"Created files: {len(created_files)}")
        self.stdout.write(f"Skipped existing files: {len(skipped_files)}")
        self.stdout.write(f"Updated config/settings/base.py: {'yes' if settings_changed else 'no'}")
        self.stdout.write(f"Updated config/urls.py: {'yes' if urls_changed else 'no'}")

    def _to_snake_case(self, name: str) -> str:
        safe = name.strip().replace("-", "_").replace(" ", "_")
        safe = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", safe)
        safe = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", safe)
        safe = re.sub(r"_+", "_", safe)
        return safe.lower().strip("_")

    def _validate_app_name(self, app_name: str) -> None:
        if not APP_NAME_PATTERN.fullmatch(app_name):
            raise CommandError("Invalid app name. Use letters, digits and underscores, starting with a letter.")
        if keyword.iskeyword(app_name):
            raise CommandError("Invalid app name. Python keywords are not allowed.")

    def _validate_api_prefix(self, api_prefix: str) -> None:
        if not api_prefix:
            raise CommandError("api-prefix cannot be empty.")
        parts = [part for part in api_prefix.split("/") if part]
        if not parts:
            raise CommandError("api-prefix must include valid path segments.")
        for part in parts:
            if not SEGMENT_PATTERN.fullmatch(part):
                raise CommandError("Invalid api-prefix segment. Allowed: lowercase letters, digits, '-' and '_'.")

    def _build_class_name(self, app_name: str) -> str:
        return "".join(part.capitalize() for part in app_name.split("_"))

    def _build_file_map(self, app_name: str, class_name: str, with_realtime: bool) -> dict[str, str]:
        files = {
            "__init__.py": "",
            "admin.py": "from django.contrib import admin\n",
            "apps.py": (
                "from django.apps import AppConfig\n\n\n"
                f"class {class_name}Config(AppConfig):\n"
                '    default_auto_field = "django.db.models.BigAutoField"\n'
                f'    name = "apps.{app_name}"\n'
                f'    label = "{app_name}"\n'
            ),
            "urls.py": (
                "from django.urls import path\n\n"
                "urlpatterns = [\n"
                "]\n"
            ),
            "migrations/__init__.py": "",
            "models/__init__.py": "",
            "selectors/__init__.py": "",
            "serializers/__init__.py": "",
            "serializers/input.py": "",
            "serializers/output.py": "",
            "services/__init__.py": "",
            "signals/__init__.py": "",
            "tasks/__init__.py": "",
            "views/__init__.py": "",
            "views/api.py": "",
        }
        if with_realtime:
            files["consumers.py"] = ""
            files["routing.py"] = (
                "from django.urls import path\n\n"
                "websocket_urlpatterns = [\n"
                "]\n"
            )
        return files

    def _ensure_list_entry(
        self,
        file_path: Path,
        list_name: str,
        canonical_entry: str,
        entry_line: str,
        dry_run: bool,
    ) -> bool:
        if not file_path.exists():
            raise CommandError(f"Required file not found: {file_path}")

        original = file_path.read_text(encoding="utf-8")
        assignment = f"{list_name} = ["
        start = original.find(assignment)
        if start == -1:
            raise CommandError(f"Could not find list assignment: {assignment} in {file_path}")

        open_bracket = original.find("[", start)
        close_bracket = self._find_matching_bracket(original, open_bracket)
        list_body = original[open_bracket + 1 : close_bracket]
        if canonical_entry in list_body:
            return False

        updated = original[:close_bracket] + f"{entry_line}\n" + original[close_bracket:]
        if dry_run:
            return True

        file_path.write_text(updated, encoding="utf-8")
        return True

    def _find_matching_bracket(self, text: str, open_index: int) -> int:
        depth = 0
        for index in range(open_index, len(text)):
            char = text[index]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return index
        raise CommandError("Malformed Python list: missing closing bracket.")
