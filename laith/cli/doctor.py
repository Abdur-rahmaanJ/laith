import os
import subprocess
import shutil
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class DoctorCheck:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = "pending"
        self.detail = ""

    def ok(self, detail: str = ""):
        self.status = "ok"
        self.detail = detail

    def warn(self, detail: str):
        self.status = "warn"
        self.detail = detail

    def fail(self, detail: str):
        self.status = "fail"
        self.detail = detail


def check_python() -> DoctorCheck:
    check = DoctorCheck("Python", "Python 3.10+ runtime")
    v = sys.version_info
    if v.major >= 3 and v.minor >= 10:
        check.ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        check.fail(f"Python {v.major}.{v.minor}.{v.micro} (need 3.10+)")
    return check


def check_jdk() -> DoctorCheck:
    check = DoctorCheck("JDK", "Java Development Kit (javac)")
    javac_path = shutil.which("javac")
    if javac_path:
        try:
            result = subprocess.run(
                ["javac", "-version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stderr.strip() or result.stdout.strip()
            check.ok(version)
        except Exception as e:
            check.warn(f"javac found but version check failed: {e}")
    else:
        check.fail("javac not found in PATH. Install JDK 17+.")
    return check


def check_java() -> DoctorCheck:
    check = DoctorCheck("Java", "Java Runtime (java)")
    java_path = shutil.which("java")
    if java_path:
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stderr.strip() or result.stdout.strip()
            check.ok(version.split("\n")[0])
        except Exception as e:
            check.warn(f"java found but version check failed: {e}")
    else:
        check.fail("java not found in PATH. Install JDK 17+.")
    return check


def check_android_sdk() -> DoctorCheck:
    check = DoctorCheck("Android SDK", "Android SDK (ANDROID_HOME)")
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        if os.path.exists(android_home):
            platforms_dir = os.path.join(android_home, "platforms")
            build_tools_dir = os.path.join(android_home, "build-tools")
            if os.path.exists(platforms_dir):
                platforms = sorted(os.listdir(platforms_dir)) if os.listdir(platforms_dir) else ["none"]
                check.ok(f"ANDROID_HOME={android_home}")
                check.detail += f" | platforms: {platforms[-1]}"
            else:
                check.warn(f"ANDROID_HOME set but platforms/ not found")
        else:
            check.fail(f"ANDROID_HOME={android_home} does not exist")
    else:
        check.fail("ANDROID_HOME not set. Set it to your Android SDK path.")
    return check


def check_adb() -> DoctorCheck:
    check = DoctorCheck("ADB", "Android Debug Bridge (adb)")
    adb_path = shutil.which("adb")
    if adb_path:
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip() or result.stderr.strip()
            first_line = version.split("\n")[0] if version else "adb found"
            check.ok(first_line)
        except Exception as e:
            check.warn(f"adb found but version check failed: {e}")
    else:
        check.fail("adb not found in PATH. Install Android SDK platform-tools.")
    return check


def check_gradle() -> DoctorCheck:
    check = DoctorCheck("Gradle", "Gradle wrapper / build system")
    gradle_path = shutil.which("gradle")
    if gradle_path:
        try:
            result = subprocess.run(
                ["gradle", "--version"],
                capture_output=True, text=True, timeout=30
            )
            for line in (result.stdout or result.stderr).split("\n"):
                if "Gradle " in line and not "Groovy" in line:
                    check.ok(line.strip())
                    break
            else:
                check.ok("gradle found")
        except Exception:
            check.ok("gradle found (version check skipped)")
    else:
        gradlew_path = shutil.which("gradlew") or (
            os.path.exists("gradlew") and "gradlew" or None
        )
        if gradlew_path:
            check.ok("Gradle wrapper (gradlew) found")
        else:
            check.warn("gradle not found globally; wrapper will be injected by laith init")
    return check


def check_laith_config(project_path: str = ".") -> DoctorCheck:
    check = DoctorCheck("laith.toml", "Laith project configuration")
    config_path = os.path.join(project_path, "laith.toml")
    if os.path.exists(config_path):
        import tomli
        try:
            with open(config_path, "rb") as f:
                data = tomli.load(f)
            if "app" in data and "name" in data["app"]:
                check.ok(f"App: {data['app']['name']}")
            else:
                check.warn("Missing [app] section or name")
        except Exception as e:
            check.fail(f"Invalid laith.toml: {e}")
    else:
        check.warn("No laith.toml found (not in a Laith project)")
    return check


def run_doctor(project_path: str = ".") -> bool:
    console.print(Panel("[bold]Laith Environment Doctor[/bold]"))
    console.print()

    checks = [
        check_python(),
        check_jdk(),
        check_java(),
        check_android_sdk(),
        check_adb(),
        check_gradle(),
        check_laith_config(project_path),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan")
    table.add_column("Status", width=10)
    table.add_column("Detail")

    all_ok = True
    for check in checks:
        status_icon = {"ok": "[green]OK[/green]", "warn": "[yellow]WARN[/yellow]", "fail": "[red]FAIL[/red]"}
        style = {"ok": "green", "warn": "yellow", "fail": "red"}
        icon = status_icon.get(check.status, "[dim]?[/dim]")
        table.add_row(
            f"{check.name}\n[dim]{check.description}[/dim]",
            icon,
            check.detail,
        )
        if check.status == "fail":
            all_ok = False

    console.print(table)
    console.print()

    if all_ok:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        console.print("[bold yellow]Some checks failed. Review the details above.[/bold yellow]")

    return all_ok
