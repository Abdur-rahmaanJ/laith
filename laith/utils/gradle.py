import subprocess
import os
import shutil
from rich.console import Console
from typing import List

console = Console()

class GradleOrchestrator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.gradlew = os.path.join(project_path, "gradlew")
        self.bin_dir = os.path.join(os.path.dirname(__file__), "..", "bin")
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    def inject_wrapper(self):
        """Inject real Gradle Wrapper (React Native style)."""
        if os.path.exists(self.gradlew) and os.path.exists(os.path.join(self.project_path, "gradle/wrapper/gradle-wrapper.jar")):
            return

        console.print("[bold yellow]Bootstrapping Gradle Wrapper...[/bold yellow]")
        
        # 1. Create directory structure
        wrapper_dir = os.path.join(self.project_path, "gradle", "wrapper")
        os.makedirs(wrapper_dir, exist_ok=True)

        # 2. Copy the launcher script
        shutil.copy2(os.path.join(self.bin_dir, "gradlew_template"), self.gradlew)
        os.chmod(self.gradlew, 0o755)

        # 3. Copy the bootstrap JAR
        shutil.copy2(
            os.path.join(self.bin_dir, "gradle-wrapper.jar_template"), 
            os.path.join(wrapper_dir, "gradle-wrapper.jar")
        )

        # 4. Create properties file from template
        with open(os.path.join(self.template_dir, "gradle-wrapper.properties.j2"), "r") as f:
            content = f.read()
        with open(os.path.join(wrapper_dir, "gradle-wrapper.properties"), "w") as f:
            f.write(content)

        console.print("[bold green]Gradle Wrapper injected successfully.[/bold green]")

    def run_task(self, task: str, args: List[str] = [], env_overrides: dict = {}) -> bool:
        if not os.path.exists(self.gradlew):
            self.inject_wrapper()

        # Use ./gradlew because we are running with cwd=self.project_path
        cmd = ["./gradlew", task] + args
        console.print(f"Executing: [bold cyan]{' '.join(cmd)}[/bold cyan] in {self.project_path}")
        
        # Prepare environment
        process_env = os.environ.copy()
        process_env.update(env_overrides)

        try:
            # Full environment build
            process = subprocess.Popen(
                cmd,
                cwd=self.project_path,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in iter(process.stdout.readline, ""):
                console.print(f"  [dim]{line.strip()}[/dim]")
            
            return process.wait() == 0
        except Exception as e:
            console.print(f"[bold red]Gradle Execution Failed:[/bold red] {str(e)}")
            return False

    def generate_signing_config(self):
        """Generate a production-ready signing configuration and keystore."""
        keystore_path = os.path.join(self.project_path, "release.keystore")
        properties_path = os.path.join(self.project_path, "keystore.properties")
        
        # 1. Generate the actual keystore binary if missing
        if not os.path.exists(keystore_path):
            console.print("[bold yellow]Generating production release keystore...[/bold yellow]")
            import subprocess
            cmd = [
                "keytool", "-genkey", "-v",
                "-keystore", keystore_path,
                "-alias", "laithkey",
                "-keyalg", "RSA",
                "-keysize", "2048",
                "-validity", "10000",
                "-storepass", "laithpassword",
                "-keypass", "laithpassword",
                "-dname", "CN=Laith Developer, OU=Engineering, O=Laith, L=Digital, S=Cloud, C=UN"
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                console.print(f"[bold green]Keystore generated:[/bold green] {keystore_path}")
            except Exception as e:
                console.print(f"[bold red]Failed to generate keystore:[/bold red] Ensure 'keytool' (JDK) is installed.")
                return

        # 2. Setup the properties file for the Gradle build
        if not os.path.exists(properties_path):
            content = f"""storeFile=../release.keystore
storePassword=laithpassword
keyAlias=laithkey
keyPassword=laithpassword
"""
            with open(properties_path, "w") as f:
                f.write(content)
            console.print(f"Signing properties synchronized at [bold green]{properties_path}[/bold green]")

    def get_apk_path(self, mode: str = "debug") -> str:
        # Standard AGP output path
        return os.path.join(self.project_path, "app", "build", "outputs", "apk", mode, f"app-{mode}.apk")
