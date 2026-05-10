@native
def fast_add(a: int, b: int) -> int:
    return a + b

def ui_entry():
    # Call the native function
    res = fast_add(10, 20)
    Column(
        Text("Native result is 30")
    )
