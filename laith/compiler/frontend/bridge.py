import subprocess
import os
import re
from typing import Dict, List, Optional, Any
from laith.compiler.frontend.symbols import Type, ANY_TYPE, VOID_TYPE, INT_TYPE, STR_TYPE, BOOL_TYPE

class BridgeManager:
    def __init__(self, sdk_path: str, platform_version: str = "android-34"):
        self.sdk_path = sdk_path
        self.jar_path = os.path.join(sdk_path, "platforms", platform_version, "android.jar")
        self.cache: Dict[str, Dict[str, Any]] = {}

    def is_available(self) -> bool:
        return os.path.exists(self.jar_path)

    def lookup_class(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Look up a class in android.jar and return its metadata."""
        if class_name in self.cache:
            return self.cache[class_name]

        if not self.is_available():
            return None

        # Try to use javap to get public methods
        try:
            # class_name might be like "android.hardware.camera2.CameraManager"
            result = subprocess.run(
                ["javap", "-classpath", self.jar_path, "-public", class_name],
                capture_output=True, text=True, check=True
            )
            metadata = self._parse_javap_output(result.stdout)
            self.cache[class_name] = metadata
            return metadata
        except subprocess.CalledProcessError:
            return None

    def _parse_javap_output(self, output: str) -> Dict[str, Any]:
        methods = {}
        # Simple regex for method signatures
        # Example: public java.lang.String[] getCameraIdList() throws ...;
        method_pattern = r"public\s+([\w\.\$\[\]<>]+)\s+(\w+)\((.*?)\)"
        
        for match in re.finditer(method_pattern, output):
            ret_type_raw = match.group(1)
            method_name = match.group(2)
            args_raw = match.group(3)
            
            # Map types
            ret_type = self._map_java_type(ret_type_raw)
            args = []
            if args_raw:
                for arg in args_raw.split(","):
                    args.append(self._map_java_type(arg.strip().split(" ")[0]))
            
            methods[method_name] = {
                "return_type": ret_type,
                "args": args
            }
            
        return {
            "methods": methods
        }

    def _map_java_type(self, java_type: str) -> Type:
        if "String" in java_type: return STR_TYPE
        if "int" in java_type or "long" in java_type: return INT_TYPE
        if "boolean" in java_type: return BOOL_TYPE
        if "void" in java_type: return VOID_TYPE
        
        # For now, return as a named type
        return Type(java_type)

    def find_class_by_short_name(self, short_name: str) -> Optional[str]:
        """Attempt to find a fully qualified class name by its short name."""
        if short_name in self.cache:
            entry = self.cache[short_name]
            if isinstance(entry, dict) and "fqn" in entry:
                return entry["fqn"]
            return None
        if not self.is_available():
            return None
        common_packages = [
            "android.content",
            "android.net",
            "android.hardware.camera2",
            "android.location",
            "android.os",
            "android.view",
            "android.widget",
            "androidx.compose.material3"
        ]
        
        for pkg in common_packages:
            fqn = f"{pkg}.{short_name}"
            metadata = self.lookup_class(fqn)
            if metadata:
                self.cache[short_name] = {"fqn": fqn, **metadata}
                return fqn
        self.cache[short_name] = {}
        return None
