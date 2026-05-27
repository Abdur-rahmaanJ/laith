import os
import tomli
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class AppIdentity:
    id: str = "com.example.laithapp"
    version_code: int = 1
    version_name: str = "1.0.0"

@dataclass
class SDKConfig:
    min: int = 24
    target: int = 34
    compile: int = 34

@dataclass
class SigningConfig:
    keystore_path: str = ""
    keystore_password: str = ""
    key_alias: str = "laithkey"
    key_password: str = ""

@dataclass
class AppConfig:
    name: str = "LaithApp"
    namespace: str = "com.example.laithapp"
    version: str = "1.0"
    identity: AppIdentity = field(default_factory=AppIdentity)
    sdk: SDKConfig = field(default_factory=SDKConfig)
    signing: SigningConfig = field(default_factory=SigningConfig)
    permissions: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=lambda: {
        "implementation": [
            "androidx.compose:compose-bom:2023.08.00",
            "androidx.core:core-ktx:1.12.0",
            "androidx.lifecycle:lifecycle-runtime-ktx:2.7.0",
            "androidx.activity:activity-compose:1.8.2",
            "androidx.compose.ui:ui",
            "androidx.compose.ui:ui-graphics",
            "androidx.compose.ui:ui-tooling-preview",
            "androidx.compose.material3:material3",
            "androidx.work:work-runtime-ktx:2.9.0",
            "org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3"
        ]
    })
    features: Dict[str, bool] = field(default_factory=lambda: {
        "compose": True,
        "native": True
    })

    def to_dict(self) -> Dict[str, Any]:
        env = os.environ
        return {
            "app_name": self.name,
            "namespace": self.namespace,
            "application_id": self.identity.id,
            "version_code": self.identity.version_code,
            "version_name": self.identity.version_name,
            "min_sdk": self.sdk.min,
            "target_sdk": self.sdk.target,
            "compile_sdk": self.sdk.compile,
            "has_native": self.features.get("native", False),
            "keystore_path": self.signing.keystore_path or env.get("LAITH_KEYSTORE_PATH", ""),
            "keystore_password": self.signing.keystore_password or env.get("LAITH_KEYSTORE_PASSWORD", ""),
            "key_alias": self.signing.key_alias or env.get("LAITH_KEY_ALIAS", "laithkey"),
            "key_password": self.signing.key_password or env.get("LAITH_KEY_PASSWORD", ""),
            "has_workers": True,
            "dependencies": self.dependencies,
            "permissions": self.permissions
        }

class ConfigManager:
    @staticmethod
    def load_from_file(file_path: str) -> AppConfig:
        if not os.path.exists(file_path): return AppConfig()
        with open(file_path, "rb") as f: data = tomli.load(f)
        config = AppConfig()
        if "app" in data:
            app = data["app"]
            config.name = app.get("name", config.name)
            config.namespace = app.get("namespace", config.namespace)
            config.permissions = app.get("permissions", [])
            if "identity" in app:
                ident = app["identity"]
                config.identity.id = ident.get("id", config.identity.id)
                config.identity.version_code = ident.get("version_code", config.identity.version_code)
                config.identity.version_name = ident.get("version_name", config.identity.version_name)
        if "sdk" in data:
            sdk = data["sdk"]; config.sdk.min = sdk.get("min", config.sdk.min)
            config.sdk.target = sdk.get("target", config.sdk.target); config.sdk.compile = sdk.get("compile", config.sdk.compile)
        if "dependencies" in data: config.dependencies.update(data["dependencies"])
        if "features" in data: config.features.update(data["features"])
        if "signing" in data:
            sig = data["signing"]
            config.signing.keystore_path = sig.get("keystore_path", config.signing.keystore_path)
            config.signing.keystore_password = sig.get("keystore_password", config.signing.keystore_password)
            config.signing.key_alias = sig.get("key_alias", config.signing.key_alias)
            config.signing.key_password = sig.get("key_password", config.signing.key_password)
        return config

    @staticmethod
    def find_and_load(start_path: str = ".") -> tuple[AppConfig, Optional[str]]:
        curr = os.path.abspath(start_path)
        if os.path.isfile(curr): curr = os.path.dirname(curr)
        while curr != os.path.dirname(curr):
            config_path = os.path.join(curr, "laith.toml")
            if os.path.exists(config_path): return ConfigManager.load_from_file(config_path), curr
            curr = os.path.dirname(curr)
        return AppConfig(), None
