# `laith doctor` — Environment Diagnostics

The `laith doctor` command checks your development environment for all prerequisites needed to build and run Laith apps.

## Usage

```bash
laith doctor
laith doctor --project /path/to/project
```

## Checks Performed

| Check | What It Verifies |
|-------|-----------------|
| **Python** | Python 3.10+ runtime is installed. |
| **JDK** | `javac` (Java compiler) is in PATH. |
| **Java** | `java` runtime is available. |
| **Android SDK** | `ANDROID_HOME` is set and the SDK platforms directory exists. |
| **ADB** | `adb` (Android Debug Bridge) is in PATH. |
| **Gradle** | Gradle or `gradlew` wrapper is available. |
| **laith.toml** | Project configuration file is valid (only if inside a project). |

## Output

The command displays a table with each check's name, status (OK/WARN/FAIL), and detail:

```
┌─────────────────────────────────┬──────────┬──────────────────────────────┐
│ Check                           │ Status   │ Detail                       │
├─────────────────────────────────┼──────────┼──────────────────────────────┤
│ Python                          │ OK       │ Python 3.12.3                │
│ Python 3.10+ runtime            │          │                              │
├─────────────────────────────────┼──────────┼──────────────────────────────┤
│ JDK                             │ OK       │ javac 17.0.9                 │
│ Java Development Kit            │          │                              │
├─────────────────────────────────┼──────────┼──────────────────────────────┤
│ ...                             │ ...      │ ...                          │
└─────────────────────────────────┴──────────┴──────────────────────────────┘
```

## Exit Code

- Returns exit code `0` (True) if all checks pass.
- Returns exit code `1` (False) if any check fails.
