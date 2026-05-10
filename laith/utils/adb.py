import subprocess
import os
from typing import List, Optional
from rich.console import Console

console = Console()

class ADBOrchestrator:
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path

    def _run_adb(self, args: List[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run([self.adb_path] + args, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]ADB Error:[/bold red] {e.stderr}")
            raise e
        except FileNotFoundError:
            console.print("[bold red]ADB not found.[/bold red] Please install Android SDK Platform-Tools.")
            raise

    def list_devices(self) -> List[str]:
        output = self._run_adb(["devices"]).stdout
        devices = []
        for line in output.splitlines()[1:]:
            if line.strip() and "\tdevice" in line:
                devices.append(line.split("\t")[0])
        return devices

    def install_apk(self, device_id: str, apk_path: str):
        console.print(f"Installing APK to [bold cyan]{device_id}[/bold cyan]...")
        self._run_adb(["-s", device_id, "install", "-r", apk_path])

    def start_activity(self, device_id: str, package_name: str, activity_name: str = ".MainActivity"):
        full_activity = f"{package_name}/{activity_name}"
        if not activity_name.startswith("."):
             full_activity = f"{package_name}/{package_name}{activity_name}"
        
        console.print(f"Starting activity [bold green]{full_activity}[/bold green]...")
        self._run_adb(["-s", device_id, "shell", "am", "start", "-n", full_activity])

    def stream_logs(self, device_id: str, package_name: str):
        console.print(f"Streaming logs for [bold yellow]{package_name}[/bold yellow] (Ctrl+C to stop)...")
        # Simple logcat filter
        process = subprocess.Popen(
            [self.adb_path, "-s", device_id, "logcat", f"{package_name}:V", "*:S"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        try:
            for line in iter(process.stdout.readline, ""):
                console.print(line.strip())
        except KeyboardInterrupt:
            process.terminate()
            console.print("\n[bold yellow]Log stream stopped.[/bold yellow]")
