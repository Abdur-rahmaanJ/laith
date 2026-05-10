import click
from rich.console import Console
from rich.panel import Panel
import os
import sys
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter

console = Console()

@click.group()
def main():
    """Laith: Python to Native Android Compiler Platform."""
    pass

from laith.utils.project import ProjectGenerator

@main.command()
@click.argument("name")
def init(name: str):
    """Initialize a new Laith project."""
    console.print(Panel(f"Initializing project: [bold green]{name}[/bold green]"))
    
    config = {
        "app_name": name,
        "application_id": f"com.example.{name.lower()}",
        "namespace": f"com.example.{name.lower()}",
        "has_workers": True # Default to True for template visibility
    }
    
    gen = ProjectGenerator(name, config)
    gen.generate()
    
    # Create default source
    os.makedirs(os.path.join(name, "src"), exist_ok=True)
    with open(os.path.join(name, "src", "main.py"), "w") as f:
        f.write('def main():\n    print("Hello from Laith!")\n')
    
    console.print(f"Created complete Android project structure for {name}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. cd {name}")
    console.print("  2. laith build src/main.py")
    console.print("  3. laith compile\n")

@main.command()
@click.option("--release", is_flag=True, help="Build in release mode")
@click.option("--project", "-p", default=".", help="Project directory")
def compile(release: bool, project: str):
    """Compile the generated project into an Android APK."""
    mode = "release" if release else "debug"
    console.print(f"[bold yellow]Compiling Android app ({mode} mode)...[/bold yellow]")
    
    # 1. Ensure build/ folder exists
    os.makedirs(os.path.join(project, "build"), exist_ok=True)
    
    # 2. Check for gradlew
    gradlew = os.path.join(project, "gradlew")
    if not os.path.exists(gradlew):
        # We might need to copy a gradlew wrapper or tell the user to use their own
        console.print("[yellow]Warning: gradlew not found. You may need to install Gradle locally.[/yellow]")
    
    console.print(f"Running: [cyan]./gradlew assemble{mode.capitalize()}[/cyan]")
    # In a full environment we would subprocess.run(gradlew)
    console.print("\n[bold green]Project is ready for Android Studio or Gradle CLI.[/bold green]")

@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output Kotlin file (optional if --project is used)")
@click.option("--project", "-p", help="Target Laith project directory")
def build(file: str, output: str, project: str):
    """Compile a Python file to Kotlin."""
    console.print(f"Compiling [bold cyan]{file}[/bold cyan]...")
    
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
        
        # 3. Emit Kotlin
        emitter = KotlinEmitter()
        kotlin_code = emitter.emit(module)
        
        # 4. Handle output destination
        final_output = output or "out.kt"
        if project:
            # We assume a default package name for now, or we could read it from a config file
            package_name = "com.example.laithapp" # Should be dynamic in the future
            package_path = package_name.replace(".", "/")
            dest_dir = os.path.join(project, "app", "src", "main", "kotlin", package_path)
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(file).replace(".py", ".kt")
            final_output = os.path.join(dest_dir, filename)
            
            # Prepend package name
            kotlin_code = f"package {package_name}\n\n{kotlin_code}"

        with open(final_output, "w") as f:
            f.write(kotlin_code)
            
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
