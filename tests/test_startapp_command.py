from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


class StartAppCommandTests(SimpleTestCase):
    def _write_project_files(self, base_dir: Path) -> None:
        (base_dir / "apps").mkdir(parents=True, exist_ok=True)
        (base_dir / "config" / "settings").mkdir(parents=True, exist_ok=True)
        (base_dir / "config" / "__init__.py").write_text("", encoding="utf-8")
        (base_dir / "config" / "settings" / "__init__.py").write_text("", encoding="utf-8")
        (base_dir / "config" / "settings" / "base.py").write_text(
            'INSTALLED_APPS = [\n    "apps.auths.apps.AuthsConfig",\n]\n',
            encoding="utf-8",
        )
        (base_dir / "config" / "urls.py").write_text(
            "from django.urls import include, path\n\n"
            "urlpatterns = [\n"
            '    path("api/v1/auth/", include("apps.auths.urls")),\n'
            "]\n",
            encoding="utf-8",
        )

    def test_startapp_creates_scaffold_inside_apps_and_registers(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self._write_project_files(base_dir)

            with self.settings(BASE_DIR=str(base_dir)):
                call_command("startapp", "socialAuth")

            app_dir = base_dir / "apps" / "social_auth"
            self.assertTrue((app_dir / "apps.py").exists())
            self.assertTrue((app_dir / "migrations" / "__init__.py").exists())
            self.assertTrue((app_dir / "serializers" / "input.py").exists())
            self.assertTrue((app_dir / "views" / "api.py").exists())

            settings_text = (base_dir / "config" / "settings" / "base.py").read_text(encoding="utf-8")
            urls_text = (base_dir / "config" / "urls.py").read_text(encoding="utf-8")
            self.assertIn("apps.social_auth.apps.SocialAuthConfig", settings_text)
            self.assertIn('include("apps.social_auth.urls")', urls_text)

    def test_startapp_blocks_duplicate_without_force(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self._write_project_files(base_dir)

            with self.settings(BASE_DIR=str(base_dir)):
                call_command("startapp", "socialAuth")
                with self.assertRaises(CommandError):
                    call_command("startapp", "socialAuth")

    def test_startapp_force_keeps_registration_idempotent(self):
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            self._write_project_files(base_dir)

            with self.settings(BASE_DIR=str(base_dir)):
                call_command("startapp", "socialAuth")
                call_command("startapp", "socialAuth", force=True)

            settings_text = (base_dir / "config" / "settings" / "base.py").read_text(encoding="utf-8")
            urls_text = (base_dir / "config" / "urls.py").read_text(encoding="utf-8")
            self.assertEqual(settings_text.count("apps.social_auth.apps.SocialAuthConfig"), 1)
            self.assertEqual(urls_text.count('include("apps.social_auth.urls")'), 1)
