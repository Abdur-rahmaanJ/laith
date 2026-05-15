import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_themed_scaffold():
    code = """
def main_ui():
    Theme(
        primary="#FF6200EE",
        dark_primary="#FFBB86FC",
        body=Scaffold(
            top_bar=TopAppBar(),
            body=Text("Themed App"),
        ),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "MaterialTheme" in kotlin_code
    assert "Scaffold" in kotlin_code
    assert "TopAppBar" in kotlin_code
    assert "lightColorScheme" in kotlin_code
    assert "darkColorScheme" in kotlin_code


def test_dialog_with_state():
    code = """
def main_ui():
    show = state(False)
    if show:
        Dialog(
            Text("Hello"),
            on_dismiss=lambda: show.set(False),
        )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Dialog" in kotlin_code
    assert "onDismissRequest" in kotlin_code


def test_preferences_integration():
    code = """
def main_ui():
    name = state("")
    prefs = Preferences("app")
    on_mount(lambda: name.set(prefs.get("saved", "")))
    TextField(value=name, on_value_change=name.set)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "getSharedPreferences" in kotlin_code
    assert "LaunchedEffect" in kotlin_code
    assert "OutlinedTextField" in kotlin_code


def test_on_resume_refresh():
    code = """
def main_ui():
    data = state("")
    on_resume(lambda: data.set("loaded"))
    Text(data)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ON_RESUME" in kotlin_code
    assert "LifecycleEventObserver" in kotlin_code


def test_effect_with_preferences():
    code = """
def main_ui():
    prefs = Preferences("app")
    count = state(0)
    effect(count, lambda old, new: prefs.set("count", new))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "getSharedPreferences" in kotlin_code


def test_file_storage_read_then_write():
    code = """
def main_ui():
    data = FileStorage.read_text("config.json")
    FileStorage.write_text("backup.json", data)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "readText" in kotlin_code
    assert "writeText" in kotlin_code


def test_snackbar_in_scaffold():
    code = """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        body=Column(
            Snackbar("Hello"),
        ),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Scaffold" in kotlin_code
    assert "TopAppBar" in kotlin_code
    assert "Snackbar" in kotlin_code


def test_navigator_push_with_route():
    code = """
def home():
    Navigator.push(settings, title="Hello")

def settings():
    pass
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "navigatorPush" in kotlin_code


def test_mounted_state_preferences():
    code = """
def main_ui():
    count = state(0)
    on_mount(lambda: print("ready"))
    effect(count, lambda old, new: print(new))
    Text(f"Count: {count}")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "Text" in kotlin_code
