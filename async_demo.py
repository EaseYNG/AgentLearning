import asyncio
import time
from datetime import datetime 

def task_a():
    time.sleep(1.0)
    print("a done")

async def task_b():
    await asyncio.sleep(2.0)
    print("b done")

async def task_c():
    await asyncio.sleep(1.0)
    print("c done")

def task_d():
    time.sleep(3.0)
    print("d done")

async def coro():
    await asyncio.gather(task_b(), task_c())

def main():
    start = datetime.now()
    task_a()
    asyncio.run(coro())
    task_d()
    end = datetime.now()
    duration = end - start
    print(f"duration: {duration}")

if __name__ == "__main__":
    main()