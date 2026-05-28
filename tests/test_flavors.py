import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from laith.utils.config import AppConfig, FlavorConfig, ConfigManager


class TestFlavorConfig:
    def test_default_no_flavors(self):
        config = AppConfig()
        assert config.flavors == {}
        d = config.to_dict()
        assert d["has_flavors"] is False
        assert d["flavors"] == {}

    def test_to_dict_includes_flavors(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""
[app]
name = "TestApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"

[flavors.dev]
application_id = "com.test.app.dev"
version_code = 2
version_name = "1.0.0-dev"
app_name = "TestApp Dev"

[flavors.staging]
application_id = "com.test.app.staging"
version_name = "1.0.0-rc"

[flavors.prod]
application_id = "com.test.app"
version_name = "1.0.0"
""")
        config = ConfigManager.load_from_file(str(toml))
        assert len(config.flavors) == 3
        assert isinstance(config.flavors["dev"], FlavorConfig)
        assert config.flavors["dev"].application_id == "com.test.app.dev"
        assert config.flavors["prod"].application_id == "com.test.app"
        assert config.flavors["staging"].version_name == "1.0.0-rc"

        d = config.to_dict()
        assert d["has_flavors"] is True
        assert set(d["flavors"].keys()) == {"dev", "staging", "prod"}

    def test_active_flavor_overrides_application_id(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""
[app]
name = "TestApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"

[flavors.dev]
application_id = "com.test.app.dev"

[flavors.prod]
application_id = "com.test.app.prod"
""")
        config = ConfigManager.load_from_file(str(toml))

        config.active_flavor = "dev"
        d = config.to_dict()
        assert d["application_id"] == "com.test.app.dev"

        config.active_flavor = "prod"
        d = config.to_dict()
        assert d["application_id"] == "com.test.app.prod"

    def test_active_flavor_missing_no_override(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""
[app]
name = "TestApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"
""")
        config = ConfigManager.load_from_file(str(toml))
        config.active_flavor = "nonexistent"
        d = config.to_dict()
        assert d["application_id"] == "com.test.app"

    def test_no_flavors_section_returns_empty(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""
[app]
name = "TestApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"
""")
        config = ConfigManager.load_from_file(str(toml))
        assert config.flavors == {}

    def test_flavor_override_keeps_defaults_intact(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""
[app]
name = "OriginalApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"
version_code = 42
version_name = "4.2.0"

[flavors.dev]
application_id = "com.test.app.dev"
app_name = "DevApp"
""")
        config = ConfigManager.load_from_file(str(toml))
        d = config.to_dict()
        assert d["application_id"] == "com.test.app"
        assert d["app_name"] == "OriginalApp"
        assert d["version_code"] == 42
        assert d["version_name"] == "4.2.0"

        config.active_flavor = "dev"
        d = config.to_dict()
        assert d["application_id"] == "com.test.app.dev"
        assert d["app_name"] == "DevApp"
        assert d["version_code"] == 42
        assert d["version_name"] == "4.2.0"

    def test_init_toml_comment_parses_correctly(self, tmp_path):
        toml = tmp_path / "test_laith.toml"
        toml.write_text("""# Laith Project Configuration
version = "1.0"

[app]
name = "TestApp"
namespace = "com.test"

[app.identity]
id = "com.test.app"
version_code = 1
version_name = "1.0.0"

[sdk]
min = 24
target = 34
compile = 34

[features]
compose = true
native = true

[flavors.dev]
application_id = "com.test.app.dev"

[flavors.prod]
application_id = "com.test.app"
""")
        config = ConfigManager.load_from_file(str(toml))
        assert len(config.flavors) == 2
        assert config.flavors["dev"].application_id == "com.test.app.dev"
        assert config.flavors["prod"].application_id == "com.test.app"
