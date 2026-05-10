from laith.compiler.ir.nodes import IRModule, IRFunction, IRValue
from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE

class JNIEmitter:
    def __init__(self, package_name: str, class_name: str = "NativeLib"):
        self.package_name = package_name
        self.class_name = class_name
        self.output = []

    def _map_jni_type(self, t) -> str:
        if t == INT_TYPE: return "jlong"
        if t == STR_TYPE: return "jstring"
        if t == BOOL_TYPE: return "jboolean"
        return "void*"

    def emit(self, module: IRModule) -> str:
        native_functions = [f for f in module.functions if any(d["name"] == "native" for d in f.decorators)]
        if not native_functions:
            return ""

        header = [
            "#include <jni.h>",
            "#include <string>",
            "extern \"C\" {"
        ]
        
        jni_methods = []
        # JNI function name format: Java_package_name_ClassName_methodName
        # Package dots replaced by underscores
        jni_package = self.package_name.replace(".", "_")
        
        for func in native_functions:
            ret_type = self._map_jni_type(func.return_type)
            func_name = f"Java_{jni_package}_{self.class_name}_{func.name}"
            
            args = ["JNIEnv* env", "jobject thiz"]
            for arg in func.args:
                args.append(f"{self._map_jni_type(arg.type)} {arg.id}")
            
            args_str = ", ".join(args)
            
            method = [
                f"JNIEXPORT {ret_type} JNICALL",
                f"{func_name}({args_str}) {{",
                f"    // Bridge to C++ implementation",
                f"    extern {ret_type} {func.name}({', '.join(self._map_jni_type(a.type) for a in func.args)});",
                f"    return {func.name}({', '.join(a.id for a in func.args)});" if func.return_type != "void" else f"    {func.name}({', '.join(a.id for a in func.args)});",
                f"}}"
            ]
            jni_methods.extend(method)
            jni_methods.append("")

        footer = ["}"]
        return "\n".join(header + [""] + jni_methods + footer)
