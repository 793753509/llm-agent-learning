import asyncio
import time


async def fetch(name: str) -> str:
    print(f"开始：{name}")
    await asyncio.sleep(1)
    print(f"完成：{name}")
    return name


async def main() -> None:
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch("A"),
        fetch("B"),
    )

    elapsed = time.perf_counter() - start
    print(results)
    print(f"耗时：{elapsed:.2f} 秒")


asyncio.run(main())