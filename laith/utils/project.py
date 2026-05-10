import os
from typing import Dict, Any

class ProjectGenerator:
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = project_path
        self.config = config
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    def generate(self):
        # 1. Create directory structure
        package_path = self.config["namespace"].replace(".", "/")
        dirs = [
            f"app/src/main/kotlin/{package_path}",
            "app/src/main/kotlin/laith/runtime",
            "app/src/main/res/values",
            "app/src/main/res/mipmap-anydpi-v26",
            "app/src/main/cpp",
            "gradle/wrapper"
        ]
        for d in dirs:
            os.makedirs(os.path.join(self.project_path, d), exist_ok=True)

        # 2. Render templates
        self._generate_file("build.gradle.kts.j2", "build.gradle.kts")
        self._generate_file("app_build.gradle.kts.j2", "app/build.gradle.kts")
        self._generate_file("AndroidManifest.xml.j2", "app/src/main/AndroidManifest.xml")
        self._generate_file("MainActivity.kt.j2", f"app/src/main/kotlin/{package_path}/MainActivity.kt")
        
        if self.config.get("has_native"):
            self._generate_file("CMakeLists.txt.j2", "app/src/main/cpp/CMakeLists.txt")
        
        with open(os.path.join(self.project_path, "settings.gradle.kts"), "w") as f:
            f.write(f'rootProject.name = "{self.config["app_name"]}"\ninclude(":app")\n')

        # 3. Copy runtime files
        runtime_src = os.path.join(os.path.dirname(__file__), "..", "..", "runtime", "android")
        runtime_dest = os.path.join(self.project_path, "app", "src", "main", "kotlin", "laith", "runtime")
        
        # Check if runtime files exist in our source tree
        if os.path.exists(runtime_src):
            import shutil
            for item in os.listdir(runtime_src):
                if item.endswith(".kt"):
                    shutil.copy2(os.path.join(runtime_src, item), os.path.join(runtime_dest, item))

    def _generate_file(self, template_name: str, output_name: str):
        with open(os.path.join(self.template_dir, template_name), "r") as f:
            content = f.read()
        
        # Simple template rendering
        for key, value in self.config.items():
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        
        # Handle simple conditionals for workers
        if "{% if has_workers %}" in content:
            if self.config.get("has_workers"):
                content = content.replace("{% if has_workers %}", "").replace("{% endif %}", "")
            else:
                import re
                content = re.sub(r"{% if has_workers %}.*?{% endif %}", "", content, flags=re.DOTALL)

        with open(os.path.join(self.project_path, output_name), "w") as f:
            f.write(content)
