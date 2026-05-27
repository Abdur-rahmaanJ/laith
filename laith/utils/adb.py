import subprocess
import os
import time
from typing import List, Optional, Dict
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

    def get_device_abi(self, device_id: str) -> str:
        """Get the primary ABI of the device."""
        return self._run_adb(["-s", device_id, "shell", "getprop", "ro.product.cpu.abi"]).stdout.strip()

    def install_apk(self, device_id: str, apk_path: str):
        console.print(f"Installing APK to [bold cyan]{device_id}[/bold cyan]...")
        # Don't capture output for install so user can see progress if adb provides it
        subprocess.run([self.adb_path, "-s", device_id, "install", "-r", apk_path], check=True)
        console.print("[bold green]Install Successful![/bold green]")

    def start_activity(self, device_id: str, package_name: str, activity_name: str = ".MainActivity"):
        full_activity = f"{package_name}/{activity_name}"
        if not activity_name.startswith("."):
             full_activity = f"{package_name}/{package_name}{activity_name}"
        
        console.print(f"Starting activity [bold green]{full_activity}[/bold green]...")
        self._run_adb(["-s", device_id, "shell", "am", "start", "-n", full_activity])

    def hot_reload(self, device_id: str, package_name: str, project_path: str):
        """Apply hot reload using Android's applyChanges or activity restart."""
        console.print(f"Hot reloading on [bold cyan]{device_id}[/bold cyan]...")
        
        # Strategy 1: Try applyChanges (Android 11+)
        try:
            result = self._run_adb(["-s", device_id, "shell", "am", "apply-changes", package_name])
            if result.returncode == 0:
                console.print("[bold green]ApplyChanges succeeded![/bold green]")
                return
        except Exception:
            pass
        
        # Strategy 2: Force-stop and restart the activity
        console.print("[yellow]Falling back to activity restart...[/yellow]")
        try:
            self._run_adb(["-s", device_id, "shell", "am", "force-stop", package_name])
            time.sleep(1)
            self.start_activity(device_id, package_name)
            console.print("[bold green]Activity restarted with new code.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Hot reload failed:[/bold red] {e}")
            raise

    def stream_logs(self, device_id: str, package_name: str, project_path: Optional[str] = None):
        console.print(f"Streaming logs for [bold yellow]{package_name}[/bold yellow] (Ctrl+C to stop)...")
        
        # Load source maps if project_path provided (Phase 8)
        source_maps = {}
        if project_path:
             map_dir = os.path.join(project_path, ".laith", "maps")
             if os.path.exists(map_dir):
                  for map_file in os.listdir(map_dir):
                       if map_file.endswith(".map"):
                            orig_file = map_file.replace(".map", "")
                            with open(os.path.join(map_dir, map_file), "r") as f:
                                 m = {}
                                 for line in f:
                                      parts = line.strip().split(":")
                                      if len(parts) == 2:
                                           m[int(parts[0])] = int(parts[1])
                                 source_maps[orig_file.replace(".py", ".kt")] = (orig_file, m)

        # Simple logcat filter
        process = subprocess.Popen(
            [self.adb_path, "-s", device_id, "logcat", f"{package_name}:V", "AndroidRuntime:E", "*:S"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        import re
        try:
            for line in iter(process.stdout.readline, ""):
                rewritten_line = line.strip()
                
                # Rewriting at package.func(main.kt:45) -> (main.py:23)
                match = re.search(r"\((\w+\.kt):(\d+)\)", rewritten_line)
                if match:
                     kt_file, kt_line = match.group(1), int(match.group(2))
                     if kt_file in source_maps:
                          py_file, mapping = source_maps[kt_file]
                          if kt_line in mapping:
                               py_line = mapping[kt_line]
                               # Highlight in green to show it's mapped back
                               rewritten_line = rewritten_line.replace(f"({kt_file}:{kt_line})", f"([bold green]{py_file}:{py_line}[/bold green])")
                
                console.print(rewritten_line)
        except KeyboardInterrupt:
            process.terminate()
            console.print("\n[bold yellow]Log stream stopped.[/bold yellow]")
