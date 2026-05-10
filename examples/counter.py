def counter_ui():
    count = state(0)
    
    Column(
        Text("Current count:"),
        Text(count.value),
        Button("Increment", on_click=lambda: count.set(count.value + 1))
    )
