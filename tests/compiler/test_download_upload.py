import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestDownloadUpload:
    def test_download_emitted(self, fresh_emitter):
        code = """
def main_ui():
    http.download("https://example.com/file.zip", "/tmp/file.zip")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "httpDownload" in kotlin
        assert "suspend fun httpDownload" in kotlin
        assert "contentLength" in kotlin
        assert "conn.requestMethod = \"GET\"" in kotlin

    def test_upload_emitted(self, fresh_emitter):
        code = """
def main_ui():
    http.upload("https://example.com/upload", "/tmp/file.txt")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "httpUpload" in kotlin
        assert "suspend fun httpUpload" in kotlin
        assert "Content-Type" in kotlin
        assert "conn.requestMethod = \"POST\"" in kotlin

    def test_download_with_progress(self, fresh_emitter):
        code = """
def show_progress(pct):
    print(pct)

def main_ui():
    http.download("https://example.com/file.zip", "/tmp/file.zip", on_progress=show_progress)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "httpDownload" in kotlin
        assert "::showProgress" in kotlin

    def test_upload_with_progress(self, fresh_emitter):
        code = """
def show_progress(pct):
    print(pct)

def main_ui():
    http.upload("https://example.com/upload", "/tmp/file.txt", on_progress=show_progress)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "httpUpload" in kotlin
        assert "::showProgress" in kotlin

    def test_http_not_emitted_when_not_used(self, fresh_emitter):
        code = """
def main_ui():
    Text("hello")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "httpDownload" not in kotlin
        assert "httpUpload" not in kotlin
