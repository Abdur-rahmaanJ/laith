import os
import pytest
from laith.utils.config import AppConfig, SigningConfig, ConfigManager
from laith.utils.project import ProjectGenerator


def test_signing_config_defaults():
    config = AppConfig()
    assert config.signing.keystore_path == ""
    assert config.signing.key_alias == "laithkey"


def test_signing_config_custom():
    config = AppConfig()
    config.signing.keystore_path = "/tmp/release.keystore"
    config.signing.keystore_password = "secret"
    config.signing.key_alias = "mykey"
    config.signing.key_password = "pass123"

    d = config.to_dict()
    assert d["keystore_path"] == "/tmp/release.keystore"
    assert d["keystore_password"] == "secret"
    assert d["key_alias"] == "mykey"


def test_signing_config_env_fallback(monkeypatch):
    monkeypatch.setenv("LAITH_KEYSTORE_PATH", "/env/keystore.jks")
    monkeypatch.setenv("LAITH_KEYSTORE_PASSWORD", "envpass")

    config = AppConfig()
    d = config.to_dict()
    assert d["keystore_path"] == "/env/keystore.jks"
    assert d["keystore_password"] == "envpass"


def test_proguard_template_exists():
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "laith", "templates", "proguard-rules.pro.j2"
    )
    assert os.path.exists(template_path)


def test_project_generator_creates_proguard(tmp_path):
    config = AppConfig(name="TestApp", namespace="com.example.test")
    d = config.to_dict()
    d["app_name"] = "TestApp"

    gen = ProjectGenerator(str(tmp_path), d)
    gen.generate()

    proguard_path = tmp_path / "app" / "proguard-rules.pro"
    assert proguard_path.exists()
    content = proguard_path.read_text()
    assert "Laith" in content
    assert "com.example.test" in content
