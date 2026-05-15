import pytest
from laith.compiler.backend.kotlin.emitter import snake_to_camel, readable_name, KotlinEmitter
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.ir.nodes import IRValue
from laith.compiler.frontend.symbols import ANY_TYPE


def test_snake_to_camel():
    assert snake_to_camel("hello_world") == "helloWorld"
    assert snake_to_camel("my_function_name") == "myFunctionName"
    assert snake_to_camel("single") == "single"
    assert snake_to_camel("alreadyCamel") == "alreadyCamel"
    assert snake_to_camel("") == ""
    assert snake_to_camel("on_click") == "onClick"


def test_readable_name_registered():
    registry = {"foo": "myVar", "bar": "count"}
    assert readable_name("foo", registry) == "myVar"
    assert readable_name("bar", registry) == "count"


def test_readable_name_unregistered():
    registry = {}
    assert readable_name("context", registry) == "context"
    assert readable_name("void", registry) == "void"
    assert readable_name("self", registry) == "self"
    assert readable_name("0", registry) == "v_0"
    assert readable_name("42", registry) == "v_42"


def test_readable_name_fun_ref():
    registry = {}
    assert readable_name("fun_ref_myFunc", registry) == "myFunc"


def test_function_camel_case():
    code = """
def my_function(a: int, b: int) -> int:
    return a + b
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "fun myFunction" in kotlin_code
    assert "myFunction(a: Int, b: Int): Int" in kotlin_code
    assert "return" in kotlin_code


def test_call_camel_case():
    code = """
def add_numbers(x: int, y: int) -> int:
    return x + y

def compute():
    return add_numbers(1, 2)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "fun addNumbers" in kotlin_code
    assert "fun compute" in kotlin_code
    assert "addNumbers(" in kotlin_code


def test_parameter_names_preserved():
    code = """
def greet(user_name: str, message_text: str) -> str:
    result = user_name + message_text
    return result
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "userName" in kotlin_code or "user_name" in kotlin_code
    assert "messageText" in kotlin_code or "message_text" in kotlin_code
    assert "fun greet" in kotlin_code


def test_source_map_comments():
    code = """
def compute():
    x = 10
    return x
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "from Python line" in kotlin_code
    source_map = emitter.get_source_map()
    assert len(source_map) > 0


def test_ui_component_camel_case():
    code = """
def main_ui():
    Column(
        Text("Hello")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "@Composable" in kotlin_code
    assert "fun mainUi" in kotlin_code


def test_snake_to_camel_backend_async():
    code = """
async def fetch_data():
    return "done"
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "suspend fun fetchData" in kotlin_code
