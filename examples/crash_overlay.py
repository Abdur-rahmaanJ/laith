"""
Example: Crash Overlay (RedBox-style)

When an uncaught exception occurs during UI composition (e.g., a bug in your
Python code that causes a runtime error), Laith catches it and displays a
full-screen crash overlay with:

- The error message
- The full stack trace in a monospace font
- A "Reload App" button that restarts the Activity

This is a development-only feature that helps you spot and fix errors
quickly — no more digging through logcat or wondering why the screen
went blank.

The crash overlay is automatically enabled in every Laith project. To
trigger it for testing, introduce an error in your code:

    def main_ui():
        x = 1 / 0         # ZeroDivisionError
        Text(f"Result: {x}")

When this code runs, the crash overlay will appear with the error details
instead of the app crashing silently.
"""
