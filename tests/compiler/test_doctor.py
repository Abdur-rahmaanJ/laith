import os
import sys
import pytest
from laith.cli.doctor import (
    check_python, check_jdk, check_java,
    check_android_sdk, check_adb, check_gradle,
    check_laith_config, DoctorCheck,
)


def test_doctor_check_ok():
    c = DoctorCheck("Test", "A test check")
    assert c.status == "pending"
    c.ok("All good")
    assert c.status == "ok"
    assert c.detail == "All good"


def test_doctor_check_warn():
    c = DoctorCheck("Test", "A test check")
    c.warn("Something off")
    assert c.status == "warn"


def test_doctor_check_fail():
    c = DoctorCheck("Test", "A test check")
    c.fail("Something wrong")
    assert c.status == "fail"


def test_python_check():
    check = check_python()
    assert check.status == "ok"
    assert "Python" in check.detail


def test_laith_config_found():
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.exists(os.path.join(project_path, "laith.toml")):
        check = check_laith_config(project_path)
        assert check.status in ("ok", "warn")


def test_laith_config_not_found():
    check = check_laith_config("/tmp")
    assert check.status == "warn"


def test_doctor_run_no_project():
    from laith.cli.doctor import run_doctor
    result = run_doctor("/tmp/nonexistent")
    assert isinstance(result, bool)


def test_check_names():
    checks = [
        check_python(),
        check_android_sdk(),
        check_gradle(),
        check_laith_config("/tmp"),
    ]
    for c in checks:
        assert c.name
        assert c.description
