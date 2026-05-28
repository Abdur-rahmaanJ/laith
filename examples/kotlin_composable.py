"""
Example: KotlinComposable — call any Jetpack Compose composable from Laith

KotlinComposable lets you call arbitrary Kotlin composable functions that are
not yet wrapped by the Laith stdlib. You pass the fully-qualified function
name as the first positional argument, followed by keyword arguments that
become the composable's parameters.

Usage:
    KotlinComposable("com.example.MyScreen", title="Hello", count=42)

This generates:
    com.example.MyScreen(title = v__t0, count = v__t1)

Use cases:
    - Call third-party library composables (Maps, Charts, etc.)
    - Call project-specific composables written in Kotlin
    - Gradual migration path: write screens in Kotlin, call from Laith
"""
