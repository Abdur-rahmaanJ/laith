from laith import state, Column, Text, Button

class AppState:
    def __init__(self):
        self.count = state(0)
    
    def increment(self):
        self.count.set(self.count.value + 1)
    
    def reset(self):
        self.count.set(0)

# Global instance
app = AppState()

def main_ui():
    Column(
        Text("Object-Oriented Counter"),
        Text(f"Count: {app.count.value}"),
        Button("Increment", on_click=lambda: app.increment()),
        Button("Reset", on_click=lambda: app.reset())
    )
