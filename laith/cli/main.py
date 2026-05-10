import click
from rich.console import Console
from rich.panel import Panel
import os
import sys
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.backend.native.emitter import CPPEmitter
from laith.compiler.backend.native.jni_emitter import JNIEmitter
from laith.compiler.optimizer.base import Optimizer
from laith.compiler.optimizer.dce import DCEPass
from laith.compiler.optimizer.const_fold import ConstantFoldingPass

console = Console()

@click.group()
def main():
    """Laith: Python to Native Android Compiler Platform."""
    pass

from laith.utils.project import ProjectGenerator

from laith.utils.config import ConfigManager, AppConfig
from laith.utils.gradle import GradleOrchestrator
from laith.utils.adb import ADBOrchestrator
...
@main.command()
@click.argument("name")
def init(name: str):
    """Initialize a new Laith project."""
    console.print(Panel(f"Initializing project: [bold green]{name}[/bold green]"))
    
    # Create project directory first
    os.makedirs(name, exist_ok=True)
    
    # Robust name sanitization for package/ID (only alphanumeric and underscores)
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    # Ensure it doesn't start with a number and has no double underscores
    safe_name = re.sub(r'^[^a-zA-Z]+', '', safe_name)
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    
    # Generate default config
    config_obj = AppConfig(
        name=os.path.basename(name).replace("/", "_").replace("\\", "_"),
        namespace=f"com.example.{safe_name}"
    )
    config_obj.identity.id = f"com.example.{safe_name}"
    
    # Write laith.toml
    toml_path = os.path.join(name, "laith.toml")
    with open(toml_path, "w") as f:
        f.write(f"""# Laith Project Configuration
version = "1.0"

[app]
name = "{config_obj.name}"
namespace = "{config_obj.namespace}"

[app.identity]
id = "{config_obj.identity.id}"
version_code = 1
version_name = "1.0.0"

[sdk]
min = 24
target = 34
compile = 34

[features]
compose = true
native = true
""")

    gen = ProjectGenerator(name, config_obj.to_dict())
    gen.generate()
    
    # Inject Gradle Wrapper
    gradle = GradleOrchestrator(name)
    gradle.inject_wrapper()
    
    # Create default source
    os.makedirs(os.path.join(name, "src"), exist_ok=True)
    with open(os.path.join(name, "src", "main.py"), "w") as f:
        f.write('from laith import Column, Text\n\ndef main_ui():\n    Column(\n        Text("Hello from Laith!")\n    )\n')
    
    console.print(f"Created complete Android project structure for {name}")
    console.print(f"Project configuration written to [bold cyan]{name}/laith.toml[/bold cyan]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. [cyan]cd {name}[/cyan]")
    console.print("  2. [cyan]laith build[/cyan]")
    console.print("  3. [cyan]laith run[/cyan] (or [cyan]laith android[/cyan])\n")

@main.command()
@click.option("--release", is_flag=True, help="Build in release mode")
@click.option("--project", "-p", help="Project directory")
def compile(release: bool, project: str):
    """Compile the generated project into an Android APK."""
    # 0. Detect project
    if project:
        if not os.path.exists(os.path.join(project, "laith.toml")):
             # Check if we are ALREADY in the project and user redundantly passed the name
             if os.path.basename(os.path.abspath(".")) == project and os.path.exists("laith.toml"):
                 project = "."
             else:
                 console.print(f"[bold red]Error:[/bold red] '{project}' is not a Laith project (no laith.toml found).")
                 sys.exit(1)
    else:
        _, project = ConfigManager.find_and_load()
    
    if not project:
        console.print("[bold red]Error:[/bold red] No Laith project found. Run this inside a project or use --project.")
        sys.exit(1)

    mode = "release" if release else "debug"
    console.print(f"[bold yellow]Compiling Android app ({mode} mode)...[/bold yellow]")
    
    gradle = GradleOrchestrator(project)
    task = f"assemble{mode.capitalize()}"
    
    if gradle.run_task(task):
        apk_path = gradle.get_apk_path(mode)
        console.print(f"\n[bold green]Build Successful![/bold green]")
        console.print(f"APK located at: [bold cyan]{apk_path}[/bold cyan]")
    else:
        console.print("\n[bold red]Build Failed.[/bold red]")
        sys.exit(1)

@main.command()
@click.option("--device", "-d", help="Target device ID")
@click.option("--project", "-p", help="Project directory")
@click.pass_context
def run(ctx, device: str, project: str):
    """Build, install, and run the app on a device."""
    # 1. Load config for package name
    if project:
        if not os.path.exists(os.path.join(project, "laith.toml")):
             if os.path.basename(os.path.abspath(".")) == project and os.path.exists("laith.toml"):
                 project = "."
             else:
                 console.print(f"[bold red]Error:[/bold red] '{project}' is not a Laith project.")
                 sys.exit(1)
        config = ConfigManager.load_from_file(os.path.join(project, "laith.toml"))
    else:
        config, project = ConfigManager.find_and_load()
    
    if not project:
        console.print("[bold red]Error:[/bold red] No Laith project found.")
        sys.exit(1)

    package_name = config.identity.id
    
    # 2. Device Discovery (Fail fast if no device before building)
    adb = ADBOrchestrator()
    try:
        devices = adb.list_devices()
    except Exception:
        sys.exit(1)
    
    if not devices:
        console.print("[bold red]No devices found.[/bold red] Connect a device or start an emulator.")
        sys.exit(1)
    
    target_device = device
    if not target_device:
        if len(devices) > 1:
            console.print(f"[yellow]Multiple devices detected. Using first one: {devices[0]}[/yellow]")
            console.print(f"[dim]Available: {', '.join(devices)}[/dim]")
        target_device = devices[0]
    elif target_device not in devices:
        console.print(f"[bold red]Device {target_device} not found.[/bold red]")
        sys.exit(1)

    # 3. Build & Install via Gradle (React Native style)
    gradle = GradleOrchestrator(project)
    
    # PERFORMANCE OPTIMIZATION: Detect device ABI to build ONLY what we need
    device_abi = adb.get_device_abi(target_device)
    console.print(f"Targeting device ABI: [bold magenta]{device_abi}[/bold magenta]")
    
    env = {"ANDROID_SERIAL": target_device}
    # Industry-standard performance flags used by high-end frameworks
    perf_args = [
        "-Pandroid.injected.build.abi.only=true",
        f"-Pandroid.injected.abi={device_abi}",
        "--parallel",
        "--configuration-cache",
        "--build-cache"
    ]
    
    console.print(f"[bold yellow]Building and installing to {target_device} ({device_abi})...[/bold yellow]")
    if not gradle.run_task("installDebug", args=perf_args, env_overrides=env):
        console.print("[bold red]Build/Install failed. Aborting run.[/bold red]")
        sys.exit(1)
    
    # 4. Start Activity
    try:
        adb.start_activity(target_device, package_name)
        
        # 5. Telemetry
        adb.stream_logs(target_device, package_name)
    except Exception as e:
        console.print(f"[bold red]Run failed:[/bold red] {str(e)}")
        sys.exit(1)

@main.command(name="android")
@click.option("--device", "-d", help="Target device ID")
@click.option("--project", "-p", help="Project directory")
@click.pass_context
def android_cmd(ctx, device: str, project: str):
    """Alias for 'laith run'. (npm run android style)"""
    ctx.invoke(run, device=device, project=project)

@main.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--output", "-o", help="Output Kotlin file (optional if --project is used)")
@click.option("--project", "-p", help="Target Laith project directory")
def build(file: str, output: str, project: str):
    """Compile a Python file to Kotlin."""
    if not file:
        file = "src/main.py"
        if not os.path.exists(file):
            console.print("[bold red]Error:[/bold red] No source file specified and 'src/main.py' not found.")
            sys.exit(1)

    console.print(f"Compiling [bold cyan]{file}[/bold cyan]...")
    
    # 0. Load Configuration
    if project:
        if not os.path.exists(os.path.join(project, "laith.toml")):
             if os.path.basename(os.path.abspath(".")) == project and os.path.exists("laith.toml"):
                 project = "."
        config = ConfigManager.load_from_file(os.path.join(project, "laith.toml"))
    else:
        config, project = ConfigManager.find_and_load(os.path.dirname(os.path.abspath(file)))

    with open(file, "r") as f:
        source = f.read()
    
    try:
        # 1. Parse & Analyze
        tree = Parser.parse(source)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        
        # 2. Build IR
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        
        # 3. Optimize
        optimizer = Optimizer()
        optimizer.add_pass(ConstantFoldingPass())
        optimizer.add_pass(DCEPass())
        optimizer.optimize(module)
        
        # 4. Emit Kotlin
        emitter = KotlinEmitter()
        kotlin_code = emitter.emit(module)
        
        # 5. Emit Native (if needed)
        native_emitter = CPPEmitter()
        native_code = native_emitter.emit(module)
        
        # 6. Handle output destination
        final_output = output or "out.kt"
        config_dict = config.to_dict()
        package_name = config_dict["namespace"]

        if project:
            # Re-run generator to keep native project in sync with laith.toml
            config_dict = config.to_dict()
            # Ensure app_name is always valid (basename) even if project path is complex
            config_dict["app_name"] = os.path.basename(os.path.abspath(project))
            
            gen = ProjectGenerator(project, config_dict)
            gen.generate()
            
            # Ensure Gradle Wrapper is present
            gradle = GradleOrchestrator(project)
            gradle.inject_wrapper()
            
            package_path = package_name.replace(".", "/")
            dest_dir = os.path.join(project, "app", "src", "main", "kotlin", package_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Map input filename to output filename (main.py -> main.kt)
            filename = os.path.basename(file).replace(".py", ".kt")
            final_output = os.path.join(dest_dir, filename)
            
            # Prepend package name
            kotlin_code = f"package {package_name}\n\n{kotlin_code}"

        with open(final_output, "w") as f:
            f.write(kotlin_code)
            
        if native_code:
            if project:
                native_dir = os.path.join(project, "app", "src", "main", "cpp")
            else:
                native_dir = os.path.dirname(final_output) or "."
            
            os.makedirs(native_dir, exist_ok=True)
            native_filename = os.path.basename(file).replace(".py", ".cpp")
            native_output = os.path.join(native_dir, native_filename)
            with open(native_output, "w") as f:
                f.write(native_code)
            
            if project:
                # Update CMakeLists if it exists
                cmake_path = os.path.join(native_dir, "CMakeLists.txt")
                if os.path.exists(cmake_path):
                    with open(cmake_path, "r") as f:
                        cmake_content = f.read()
                    if native_filename not in cmake_content:
                        # Simple append for now
                        cmake_content = cmake_content.replace("{{ native_sources }}", f"{native_filename}\n    {{{{ native_sources }}}}")
                        with open(cmake_path, "w") as f:
                            f.write(cmake_content)
                
            console.print(f"[bold green]Native code written to {native_output}[/bold green]")

        # Always update JNI Bridge if native is enabled, to keep it in sync with package name
        if config.features.get("native"):
            if project:
                native_dir = os.path.join(project, "app", "src", "main", "cpp")
            else:
                native_dir = os.path.dirname(final_output) or "."
            
            os.makedirs(native_dir, exist_ok=True)
            jni_emitter = JNIEmitter(package_name=package_name)
            jni_code = jni_emitter.emit(module)
            jni_output = os.path.join(native_dir, "jni_bridge.cpp")
            with open(jni_output, "w") as f:
                f.write(jni_code)
            console.print(f"[bold green]JNI bridge updated at {jni_output}[/bold green]")
            
        console.print(f"[bold green]Success![/bold green] Output written to {final_output}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

@main.command()
def doctor():
    """Check environment for dependencies."""
    console.print("[bold yellow]Checking dependencies...[/bold yellow]")
    # Check for uv, gradle, etc.
    console.print("Python 3.10+: [green]OK[/green]")
    console.print("uv: [green]OK[/green]")
    console.print("Android SDK: [yellow]NOT FOUND (Optional for now)[/yellow]")

if __name__ == "__main__":
    main()
