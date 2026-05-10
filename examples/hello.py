def hello(name: str) -> str:
    msg = "Hello, " + name
    return msg

async def main():
    res = hello("Laith")
    print(res)
