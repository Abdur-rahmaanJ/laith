import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.ir.nodes import NavigatorPush, NavigatorPop


def test_navigator_push_ir():
    code = """
def settings():
    pass

def main_ui():
    Navigator.push(settings)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    main_ui = next(f for f in module.functions if f.name == "main_ui")
    assert main_ui is not None
    insts = main_ui.blocks[0].instructions
    assert any(isinstance(i, NavigatorPush) for i in insts)
    push_inst = next(i for i in insts if isinstance(i, NavigatorPush))
    assert push_inst.screen_func == "settings"


def test_navigator_push_with_params():
    code = """
def profile():
    pass

def main_ui():
    Navigator.push(profile, user_id=10, name="test")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    main_ui = next(f for f in module.functions if f.name == "main_ui")
    insts = main_ui.blocks[0].instructions
    push_inst = next(i for i in insts if isinstance(i, NavigatorPush))
    assert push_inst.screen_func == "profile"
    assert "user_id" in push_inst.kwargs
    assert "name" in push_inst.kwargs


def test_navigator_pop_ir():
    code = """
def main_ui():
    Navigator.pop()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    main_ui = next(f for f in module.functions if f.name == "main_ui")
    insts = main_ui.blocks[0].instructions
    assert any(isinstance(i, NavigatorPop) for i in insts)


def test_navigator_pop_with_result():
    code = """
def main_ui():
    Navigator.pop("done")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    main_ui = next(f for f in module.functions if f.name == "main_ui")
    insts = main_ui.blocks[0].instructions
    pop_inst = next(i for i in insts if isinstance(i, NavigatorPop))
    assert pop_inst.result is not None


def test_navigator_push_kotlin_emission():
    code = """
def settings():
    pass

def main_ui():
    Navigator.push(settings)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "navigatorPush" in kotlin_code


def test_navigator_pop_kotlin_emission():
    code = """
def main_ui():
    Navigator.pop()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "navigatorPop" in kotlin_code


def test_route_decorator():
    code = """
@route(path="/settings")
def settings_screen():
    pass
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    settings = next(f for f in module.functions if f.name == "settings_screen")
    route_dec = next((d for d in settings.decorators if d["name"] == "route"), None)
    assert route_dec is not None
    assert route_dec["args"]["path"] == "/settings"


def test_route_decorator_kotlin_emission():
    code = """
@route(path="/settings")
def settings_screen():
    pass
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert '@Route("/settings")' in kotlin_code
    assert "settingsScreen" in kotlin_code


def test_navigator_integration():
    code = """
def home():
    pass

@route(path="/profile")
def profile():
    Navigator.push(home)
    Navigator.pop()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "navigatorPush" in kotlin_code
    assert "navigatorPop" in kotlin_code
    assert "profile" in kotlin_code or "profileScreen" in kotlin_code


def test_navigator_push_no_args_error():
    code = """
def main_ui():
    Navigator.push()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    with pytest.raises(Exception) as excinfo:
        builder.build(tree)
    assert "Navigator.push() requires a screen function name" in str(excinfo.value)
