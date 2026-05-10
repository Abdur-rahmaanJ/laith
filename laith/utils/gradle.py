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

    def inject_wrapper(self):
        """Inject a minimal Gradle Wrapper if not present."""
        if os.path.exists(self.gradlew):
            return

        console.print("[bold yellow]Injecting Gradle Wrapper...[/bold yellow]")
        # In a real tool, we would download or bundle the wrapper JAR.
        # For this prototype, we'll try to use 'gradle wrapper' if available,
        # or create a mock gradlew if we're in a restricted environment.
        try:
            subprocess.run(["gradle", "wrapper"], cwd=self.project_path, check=True, capture_output=True)
            console.print("[bold green]Gradle Wrapper injected successfully.[/bold green]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[yellow]Warning: Could not run 'gradle wrapper'. Creating a placeholder gradlew script.[/yellow]")
            with open(self.gradlew, "w") as f:
                f.write("#!/bin/bash\necho 'Please install Gradle to use this wrapper or run your local gradle command.'\n")
            os.chmod(self.gradlew, 0o755)

    def run_task(self, task: str, args: List[str] = []) -> bool:
        if not os.path.exists(self.gradlew):
            console.print("[bold red]Error: gradlew not found. Run 'laith init' or install Gradle.[/bold red]")
            return False

        # Use ./gradlew because we are running with cwd=self.project_path
        cmd = ["./gradlew", task] + args
        console.print(f"Executing: [bold cyan]{' '.join(cmd)}[/bold cyan] in {self.project_path}")
        
        try:
            # We use a real-time output streaming approach
            process = subprocess.Popen(
                cmd,
                cwd=self.project_path,
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

    def get_apk_path(self, mode: str = "debug") -> str:
        # Standard AGP output path
        return os.path.join(self.project_path, "app", "build", "outputs", "apk", mode, f"app-{mode}.apk")
