import os
from typing import Dict, Any, Set
from jinja2 import Environment, FileSystemLoader

class ProjectGenerator:
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = project_path
        self.config = config
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate(self):
        package_path = self.config["namespace"].replace(".", "/")
        dirs = [f"app/src/main/kotlin/{package_path}", "app/src/main/kotlin/laith/runtime", "app/src/main/res/values",
                "app/src/main/res/mipmap-anydpi-v26", "app/src/main/cpp", "gradle/wrapper"]
        for d in dirs: os.makedirs(os.path.join(self.project_path, d), exist_ok=True)

        self._generate_file("build.gradle.kts.j2", "build.gradle.kts")
        self._generate_file("app_build.gradle.kts.j2", "app/build.gradle.kts")
        self._generate_file("AndroidManifest.xml.j2", "app/src/main/AndroidManifest.xml")
        self._generate_file("MainActivity.kt.j2", f"app/src/main/kotlin/{package_path}/MainActivity.kt")
        self._generate_file("themes.xml.j2", "app/src/main/res/values/themes.xml")
        self._generate_file("colors.xml.j2", "app/src/main/res/values/colors.xml")
        self._generate_file("ic_launcher.xml.j2", "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml")
        self._generate_file("ic_launcher.xml.j2", "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml")
        
        self._generate_file("proguard-rules.pro.j2", "app/proguard-rules.pro")

        if self.config.get("has_native"):
            self._generate_file("CMakeLists.txt.j2", "app/src/main/cpp/CMakeLists.txt")
            jni_dest = os.path.join(self.project_path, "app", "src", "main", "cpp", "jni_bridge.cpp")
            if not os.path.exists(jni_dest): self._write_file(jni_dest, '#include <jni.h>\nextern "C" {\n}\n')
        
        self._write_file(os.path.join(self.project_path, "settings.gradle.kts"), f'rootProject.name = "{self.config["app_name"]}"\ninclude(":app")\n')
        sdk_dir = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "/home/appinv/Android/Sdk"
        self._write_file(os.path.join(self.project_path, "local.properties"), f"sdk.dir={sdk_dir}\n")
        self._write_file(os.path.join(self.project_path, "gradle.properties"), "android.useAndroidX=true\nandroid.enableJetifier=true\norg.gradle.parallel=true\norg.gradle.caching=true\norg.gradle.vfs.watch=true\norg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=512m\nandroid.nonTransitiveRClass=true\nandroid.nonFinalResIds=true\n")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        runtime_src = os.path.join(base_dir, "..", "runtime", "android")
        runtime_dest = os.path.join(self.project_path, "app", "src", "main", "kotlin", "laith", "runtime")
        if os.path.exists(runtime_src):
            for item in os.listdir(runtime_src):
                if item.endswith(".kt"):
                    with open(os.path.join(runtime_src, item), "r") as f: self._write_file(os.path.join(runtime_dest, item), f.read())

    def _write_file(self, path: str, content: str):
        if os.path.exists(path):
            with open(path, "r") as f:
                if f.read() == content: return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(content)

    def _generate_file(self, template_name: str, output_name: str):
        template = self.env.get_template(template_name)
        context = self.config.copy()
        if "dependencies" in context and isinstance(context["dependencies"], dict):
            deps_str = []
            for config_name, libs in context["dependencies"].items():
                for lib in libs:
                    if "bom" in lib.lower() or "platform" in lib.lower(): deps_str.append(f'    {config_name}(platform("{lib}"))')
                    else: deps_str.append(f'    {config_name}("{lib}")')
            context["dependencies_block"] = "\n".join(deps_str)
        
        # Format permissions into a Set to avoid duplicates
        perms = set(context.get("permissions", []))
        if "inferred_permissions" in context: perms.update(context["inferred_permissions"])
        context["all_permissions"] = sorted(list(perms))

        output = template.render(**context)
        self._write_file(os.path.join(self.project_path, output_name), output)
