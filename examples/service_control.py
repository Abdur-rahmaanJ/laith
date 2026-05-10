@foreground_service(notification="Tracker")
async def tracker():
    print("Tracking...")

def ui():
    Column(
        Button("Start", on_click=lambda: start_service(tracker)),
        Button("Stop", on_click=lambda: stop_service(tracker))
    )
