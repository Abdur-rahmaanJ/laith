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
        native_methods = []
        for cls in module.classes:
            for method in cls.methods:
                if any(d["name"] == "native" for d in method.decorators):
                    native_methods.append((cls.name, method))

        header = [
            "#include <jni.h>",
            "#include <string>",
            "",
            'extern "C" {'
        ]
        
        jni_methods = []
        jni_package = self.package_name.replace(".", "_")
        
        # 1. Global Functions
        for func in native_functions:
            ret_type = self._map_jni_type(func.return_type)
            # Declared outside the JNI function but inside extern "C"
            jni_methods.append(f'    {ret_type} {func.name}({", ".join(self._map_jni_type(a.type) for a in func.args)});')
            
            func_name = f"Java_{jni_package}_{self.class_name}_{func.name}"
            args = ["JNIEnv* env", "jobject thiz"]
            for arg in func.args: args.append(f"{self._map_jni_type(arg.type)} {arg.id}")
            
            jni_methods.append(f"    JNIEXPORT {ret_type} JNICALL {func_name}({', '.join(args)}) {{")
            call_str = f"{func.name}({', '.join(a.id for a in func.args)})"
            if func.return_type.name != "void":
                jni_methods.append(f"        return {call_str};")
            else:
                jni_methods.append(f"        {call_str};")
            jni_methods.append("    }")
            jni_methods.append("")

        # 2. Class Methods (mangled)
        for cls_name, method in native_methods:
            ret_type = self._map_jni_type(method.return_type)
            mangled_impl = f"{cls_name}_{method.name}"
            jni_methods.append(f'    {ret_type} {mangled_impl}({", ".join(self._map_jni_type(a.type) for a in method.args)});')
            
            func_name = f"Java_{jni_package}_{self.class_name}_{mangled_impl}"
            args = ["JNIEnv* env", "jobject thiz"]
            for arg in method.args: args.append(f"{self._map_jni_type(arg.type)} {arg.id}")
            
            jni_methods.append(f"    JNIEXPORT {ret_type} JNICALL {func_name}({', '.join(args)}) {{")
            call_str = f"{mangled_impl}({', '.join(a.id for a in method.args)})"
            if method.return_type.name != "void":
                jni_methods.append(f"        return {call_str};")
            else:
                jni_methods.append(f"        {call_str};")
            jni_methods.append("    }")
            jni_methods.append("")

        footer = ["}"]
        return "\n".join(header + jni_methods + footer)
