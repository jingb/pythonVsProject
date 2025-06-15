import asyncio
import time


async def say_after(delay, what):
    await asyncio.sleep (delay)
    return f"{delay} - {what}"


async def main1():
    print(f"started at {time.strftime('%X')}")

    # 这个写法的话c1 是个协程类型，直接await是告诉eventloop要等它运行之后的结果，代码会卡在那里
    c1 = say_after(1, 'hello')
    c2 = say_after(2, 'hello')
    ret1 = await c1
    ret2 = await c2
    print(ret1)
    print(ret2)
    print(f"finished at {time.strftime('%X')}")



async def main():
    # coroutine 变成task的时候才会被执行
    # 极客时间里面提说 task是特殊的future 对象
    task1 = asyncio.create_task(say_after(1, 'hello'))

    task2 = asyncio.create_task(say_after(2, 'world'))

    print(f"started at {time.strftime('%X')}")
    ret1 = await task1
    ret2 = await task2

    print(ret1)
    print(ret2)
    print(f"finished at {time.strftime('%X')}")


asyncio.run(main1())
print()

asyncio.run(main())
print("注意两个写法的总耗时")