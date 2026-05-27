import pytest
from laith.compiler.backend.kotlin.emitter import snake_to_camel, readable_name


class TestNameConversion:
    def test_snake_to_camel_basic(self):
        assert snake_to_camel("hello_world") == "helloWorld"
        assert snake_to_camel("simple") == "simple"
        assert snake_to_camel("alreadyCamel") == "alreadyCamel"

    def test_snake_to_camel_edge_cases(self):
        assert snake_to_camel("a") == "a"
        assert snake_to_camel("a_b") == "aB"
        assert snake_to_camel("a_b_c") == "aBC"
        assert snake_to_camel("on_click") == "onClick"
        assert snake_to_camel("on_value_change") == "onValueChange"

    def test_snake_to_camel_empty(self):
        assert snake_to_camel("") == ""

    def test_snake_to_camel_single_underscore(self):
        assert snake_to_camel("_") == ""
        assert snake_to_camel("a_") == "a"
        assert snake_to_camel("_a") == "A"


class TestReadableName:
    def test_readable_name_fun_ref(self):
        reg = {}
        assert readable_name("fun_ref_myFunc", reg) == "myFunc"

    def test_readable_name_registered(self):
        reg = {"x": "counter"}
        assert readable_name("x", reg) == "counter"

    def test_readable_name_special(self):
        reg = {}
        special = {"context", "item", "newVal", "new_val", "granted", "lat", "lon"}
        for s in special:
            assert readable_name(s, reg) == s

    def test_readable_name_void_self(self):
        reg = {}
        assert readable_name("void", reg) == "void"
        assert readable_name("self", reg) == "self"

    def test_readable_name_uppercase(self):
        reg = {}
        assert readable_name("MyClass", reg) == "MyClass"

    def test_readable_name_generates_v_prefix(self):
        reg = {}
        result = readable_name("unknown_var", reg)
        assert result.startswith("v_")
