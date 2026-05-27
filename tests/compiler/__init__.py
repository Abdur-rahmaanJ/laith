import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestPermissions:
    def test_permission_check(self, fresh_emitter):
        code = """
def main_ui():
    granted = remember_permission("CAMERA")
    if granted:
        Text("Camera allowed")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "remember" in kotlin
        assert "PERMISSION_GRANTED" in kotlin

    def test_permission_decorator(self, fresh_emitter):
        code = """
@requires_permission(permission="CAMERA")
def main_ui():
    Text("Camera")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "checkSelfPermission" in kotlin


class TestSecureStorage:
    def test_secure_storage_get(self, fresh_emitter):
        code = """
def main_ui():
    storage = SecureStorage("app")
    val = storage.get("key", "default")
    Text(val)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "SecureStorageUtil" in kotlin or "getString" in kotlin

    def test_secure_storage_set(self, fresh_emitter):
        code = """
def main_ui():
    storage = SecureStorage("app")
    storage.set("key", "value")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "SecureStorageUtil" in kotlin or "putString" in kotlin


class TestPreferences:
    def test_preferences_get(self, fresh_emitter):
        code = """
def main_ui():
    prefs = Preferences("app")
    val = prefs.get("key", "default")
    Text(val)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "getSharedPreferences" in kotlin
        assert "getString" in kotlin

    def test_preferences_set(self, fresh_emitter):
        code = """
def main_ui():
    prefs = Preferences("app")
    prefs.set("key", "value")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "getSharedPreferences" in kotlin
        assert "putString" in kotlin or "edit" in kotlin


class TestSQLite:
    def test_query(self, fresh_emitter):
        code = """
def main_ui():
    db = Database("app.db")
    cursor = db.query("SELECT * FROM users")
    Text("queried")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "rawQuery" in kotlin or "database" in kotlin.lower()

    def test_execute(self, fresh_emitter):
        code = """
def main_ui():
    db = Database("app.db")
    db.execute("INSERT INTO users VALUES (1, 'a')")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "execSQL" in kotlin or "database" in kotlin.lower()


class TestResource:
    def test_resource_pattern(self, fresh_emitter):
        code = """
def fetch_data():
    return "data"

def main_ui():
    res = resource(fetch_data)
    Text(res)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "Resource" in kotlin


class TestReadableNames:
    def test_snake_to_camel(self):
        from laith.compiler.backend.kotlin.emitter import snake_to_camel
        assert snake_to_camel("hello_world") == "helloWorld"
        assert snake_to_camel("simple") == "simple"
        assert snake_to_camel("alreadyCamel") == "alreadyCamel"
        assert snake_to_camel("a_b_c") == "aBC"


class TestReleaseBuilds:
    def test_emitter_imports_integrity(self, fresh_emitter):
        code = """
def main_ui():
    Text("Hello")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        # Ensure no duplicate imports
        import_lines = [l for l in kotlin.split("\n") if l.startswith("import ")]
        unique_imports = set(import_lines)
        assert len(import_lines) == len(unique_imports), "Duplicate imports found"
