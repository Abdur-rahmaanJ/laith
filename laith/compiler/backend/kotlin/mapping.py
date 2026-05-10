from laith.compiler.frontend.symbols import (
    Type, INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE
)

def map_type_to_kotlin(t: Type) -> str:
    if t == INT_TYPE:
        return "Int"
    if t == STR_TYPE:
        return "String"
    if t == BOOL_TYPE:
        return "Boolean"
    if t == VOID_TYPE:
        return "Unit"
    if t == ANY_TYPE:
        return "Any?"
    
    # For now, just return the name if it's a class type
    return t.name
