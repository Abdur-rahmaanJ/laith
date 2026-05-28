import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestCrashOverlay:
    """Verify crash overlay runtime file and template integration."""

    def test_crash_overlay_kt_exists(self):
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "laith", "runtime", "android", "CrashOverlay.kt"
        )
        assert os.path.exists(path)

    def test_crash_overlay_kt_has_crash_overlay_function(self):
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "laith", "runtime", "android", "CrashOverlay.kt"
        )
        with open(path) as f:
            content = f.read()
        assert "fun CrashOverlay(content:" in content
        assert "fun stackTraceToString" in content
        assert "Reload App" in content

    def test_main_activity_template_has_crash_overlay_import(self):
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "laith", "templates", "MainActivity.kt.j2"
        )
        with open(path) as f:
            content = f.read()
        assert "import laith.runtime.CrashOverlay" in content

    def test_main_activity_template_wraps_main_ui(self):
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "laith", "templates", "MainActivity.kt.j2"
        )
        with open(path) as f:
            content = f.read()
        assert "CrashOverlay {" in content
        assert "mainUi()" in content

    def test_runtime_file_auto_copied_by_generator(self):
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "laith", "utils", "project.py"
        )
        with open(path) as f:
            content = f.read()
        # Generator copies all .kt files from runtime/android/
        assert 'if item.endswith(".kt")' in content
        assert '"runtime", "android"' in content
