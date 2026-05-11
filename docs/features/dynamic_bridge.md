# The Great Bridge: Dynamic Android API Discovery

The **Dynamic Android API Bridge** is a foundational feature of the Laith compiler. It allows developers to access the entire Android SDK directly from Python with zero manual bridging, wrappers, or JNI boilerplate.

## The Core Concept: "Native Python"

Traditional cross-platform frameworks (like React Native or Flutter) require developers to write "Platform Channels" or "Native Modules" in Java/Kotlin to expose Android-specific hardware or APIs to the high-level language.

In Laith, there is no such requirement. You simply use the Android class as if it were a native Python object:

```python
def display_device_info():
    # 'Build' is automatically discovered and linked to android.os.Build
    model = Build.MODEL
    print(f"Device Model: {model}")
```

## How It Works (The Discovery Engine)

When the compiler encounters an identifier that isn't defined in your Python code, it triggers the **Discovery Engine** (`laith/compiler/frontend/bridge.py`):

1.  **Bytecode Disassembly**: The compiler utilizes the system's `javap` utility to scan the official `android.jar` (the Android SDK library).
2.  **Fuzzy Symbol Lookup**: It searches for a matching class name within common Android packages (e.g., `android.os`, `android.view`, `android.content`).
3.  **Fully Qualified Name (FQN) Resolution**: If a match is found (e.g., `Build` -> `android.os.Build`), the compiler stores the mapping.
4.  **Static Linkage**: During the emission phase, the Kotlin backend generates direct calls to the fully qualified class. Because this is resolved at compile-time, there is **zero runtime overhead**.

## Key Advantages

### 1. Zero Boilerplate
You never have to write "Bridge" code. If an API is listed in the official Android Developer documentation, you can call it immediately from Python.

### 2. High Performance
Since the calls are statically compiled into Kotlin/JVM bytecode, your Python code interacts with the Android SDK at the same speed as a native app written in Kotlin.

### 3. Smart Permission Inference
The Bridge Manager identifies which APIs are being used. If you call an API that requires a specific Android permission (like `VIBRATOR_SERVICE`), the compiler **automatically injects** the required `<uses-permission>` tags into the generated `AndroidManifest.xml`.

## Example: Hardware Integration

```python
from laith import Text, Button, Build

def main_ui():
    # Accessing android.os.Build directly
    Text(f"Android Version: {Build.VERSION.RELEASE}")
    
    # The compiler handles nested attributes and static fields
    Text(f"Manufacturer: {Build.MANUFACTURER}")
```

## Supported Scopes
The Dynamic Bridge is available in:
*   **UI Functions**: Access context-sensitive APIs like `Vibrator`.
*   **Background Services**: Interact with system managers.
*   **Custom Classes**: Store Android objects as instance attributes.

## Advanced Usage Examples

Because The Great Bridge performs real-time analysis of the Android SDK, you can access almost any system service or hardware metadata.

### 1. Screen & Display Metrics
Access the `DisplayMetrics` class to get precise information about the user's screen density and resolution.

```python
def main_ui():
    # 'DisplayMetrics' auto-resolved to android.util.DisplayMetrics
    dm = context.getResources().getDisplayMetrics()
    
    Column(
        Text(f"Screen Density: {dm.density}"),
        Text(f"Resolution: {dm.widthPixels}x{dm.heightPixels}px")
    )
```

### 2. Battery & Power Status
Use the `BatteryManager` to check current battery percentage.

```python
def check_battery():
    # 'BatteryManager' auto-resolved to android.os.BatteryManager
    bm = context.getSystemService(Context.BATTERY_SERVICE)
    level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    
    if level < 20:
        vibrate(1000) # Warn user if battery is low
    
    print(f"Battery at {level}%")
```

### 3. System Intents (Opening URLs)
Trigger standard Android Intents to open external websites.

```python
def open_docs():
    url = "https://laith.dev"
    # 'Intent' -> android.content.Intent, 'Uri' -> android.net.Uri
    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    context.startActivity(intent)

def main_ui():
    Button("Visit Documentation", on_click=lambda: open_docs())
```

### 4. File System & Storage
Access standard Android storage paths using the `Environment` class.

```python
def log_storage_info():
    # 'Environment' -> android.os.Environment
    root = Environment.getExternalStorageDirectory().getPath()
    print(f"External Root: {root}")
```

### 5. Native Toast Notifications
Trigger lightweight system alerts.

```python
def show_alert(msg):
    # 'Toast' -> android.widget.Toast
    Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()

def main_ui():
    Button("Ping System", on_click=lambda: show_alert("System Responding!"))
```

### 6. Hardware Sensors
Register listeners for hardware sensors via bridged callbacks.

```python
def start_light_monitor():
    manager = context.getSystemService(Context.SENSOR_SERVICE)
    sensor = manager.getDefaultSensor(Sensor.TYPE_LIGHT)
    
    # Passing a Python function as a hardware listener callback
    def on_change(event):
        lux = event.values[0]
        print(f"Ambient Light: {lux}")
        
    manager.registerListener(on_change, sensor, SensorManager.SENSOR_DELAY_UI)
```
