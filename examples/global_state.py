# Global state
app_counter = state(0)

@periodic_task(interval="5s")
async def auto_inc():
    # Update global state from background
    app_counter.set(app_counter.value + 1)

def counter_ui():
    Column(
        Text("Global Count:"),
        Text(app_counter.value),
        Button("Reset", on_click=lambda: app_counter.set(0))
    )
