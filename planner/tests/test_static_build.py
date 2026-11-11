import pytest
from django.core.management import call_command


def test_collectstatic_works_with_the_production_storage(settings, tmp_path):
    """The deploy runs collectstatic with hashed (manifest) storage.

    A vendored file that points at a missing file (e.g. a `sourceMappingURL`
    comment) makes that step fail and the whole deploy with it, so run the
    same step here, where CI can catch it before it reaches the host.
    """
    settings.STATIC_ROOT = str(tmp_path / "static")
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    call_command("collectstatic", interactive=False, verbosity=0)
    assert (tmp_path / "static" / "staticfiles.json").exists()
