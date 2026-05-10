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
                with open(jni_dest, "w") as f:
                    f.write('#include <jni.h>\nextern "C" {\n}\n')
        
        with open(os.path.join(self.project_path, "settings.gradle.kts"), "w") as f:
            f.write(f'rootProject.name = "{self.config["app_name"]}"\ninclude(":app")\n')

        # Create local.properties for SDK path
        sdk_dir = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "/home/appinv/Android/Sdk"
        with open(os.path.join(self.project_path, "local.properties"), "w") as f:
            f.write(f"sdk.dir={sdk_dir}\n")

        # Create gradle.properties for AndroidX and Performance
        with open(os.path.join(self.project_path, "gradle.properties"), "w") as f:
            f.write("android.useAndroidX=true\n")
            f.write("android.enableJetifier=true\n")
            f.write("org.gradle.parallel=true\n")
            f.write("org.gradle.caching=true\n")
            f.write("org.gradle.vfs.watch=true\n")
            f.write("org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=512m\n")
            f.write("android.nonTransitiveRClass=true\n")
            f.write("android.nonFinalResIds=true\n")

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
                    shutil.copy2(src_file, dest_file)
        else:
            print(f"DEBUG: Runtime source not found at {runtime_src}")

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
                        deps_str.append(f'    {config_name}(platform("{lib}"))')
            context["dependencies_block"] = "\n".join(deps_str)

        output = template.render(**context)
        
        with open(os.path.join(self.project_path, output_name), "w") as f:
            f.write(output)
