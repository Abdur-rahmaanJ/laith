import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

class ProjectGenerator:
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = project_path
        self.config = config
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

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
        
        # Render basic resources
        self._generate_file("themes.xml.j2", "app/src/main/res/values/themes.xml")
        self._generate_file("colors.xml.j2", "app/src/main/res/values/colors.xml")
        self._generate_file("ic_launcher.xml.j2", "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml")
        self._generate_file("ic_launcher.xml.j2", "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml")
        
        if self.config.get("has_native"):
            self._generate_file("CMakeLists.txt.j2", "app/src/main/cpp/CMakeLists.txt")
            # Create a placeholder JNI bridge to satisfy CMake target requirements
            jni_dest = os.path.join(self.project_path, "app", "src", "main", "cpp", "jni_bridge.cpp")
            if not os.path.exists(jni_dest):
                self._write_file(jni_dest, '#include <jni.h>\nextern "C" {\n}\n')
        
        self._write_file(os.path.join(self.project_path, "settings.gradle.kts"), 
                        f'rootProject.name = "{self.config["app_name"]}"\ninclude(":app")\n')

        # Create local.properties for SDK path
        sdk_dir = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "/home/appinv/Android/Sdk"
        self._write_file(os.path.join(self.project_path, "local.properties"), f"sdk.dir={sdk_dir}\n")

        # Create gradle.properties for AndroidX and Performance
        properties_content = """android.useAndroidX=true
android.enableJetifier=true
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.vfs.watch=true
org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=512m
android.nonTransitiveRClass=true
android.nonFinalResIds=true
"""
        self._write_file(os.path.join(self.project_path, "gradle.properties"), properties_content)

        # 3. Copy runtime files
        # Find runtime files relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        runtime_src = os.path.join(base_dir, "..", "runtime", "android")
        runtime_dest = os.path.join(self.project_path, "app", "src", "main", "kotlin", "laith", "runtime")
        
        if os.path.exists(runtime_src):
            import shutil
            for item in os.listdir(runtime_src):
                if item.endswith(".kt"):
                    src_file = os.path.join(runtime_src, item)
                    dest_file = os.path.join(runtime_dest, item)
                    # Use our smart write logic for runtime files too
                    with open(src_file, "r") as f:
                        self._write_file(dest_file, f.read())

    def _write_file(self, path: str, content: str):
        """Write file only if content has changed to preserve timestamps."""
        if os.path.exists(path):
            with open(path, "r") as f:
                if f.read() == content:
                    return # No change, skip write
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    def _generate_file(self, template_name: str, output_name: str):
        # Use Jinja2 to render the template
        template = self.env.get_template(template_name)
        
        # Prepare context
        context = self.config.copy()
        
        # 1. Prepare dependencies block for Kotlin DSL
        if "dependencies" in context and isinstance(context["dependencies"], dict):
            deps_str = []
            for config_name, libs in context["dependencies"].items():
                for lib in libs:
                    # Robust BOM detection: coordinates containing 'bom' or 'platform'
                    if "bom" in lib.lower() or "platform" in lib.lower():
                        deps_str.append(f'    {config_name}(platform("{lib}"))')
                    elif ":" in lib:
                        deps_str.append(f'    {config_name}("{lib}")')
                    else:
                        # Fallback for short names if we ever use them
                        deps_str.append(f'    {config_name}(platform("{lib}"))')
            context["dependencies_block"] = "\n".join(deps_str)

        output = template.render(**context)
        self._write_file(os.path.join(self.project_path, output_name), output)
