import asyncio
tasks=[]
name=["1","2"]
# 定义一个协程，返回一个值
async def task1(name):
    
    print("{name}任务开始执行")
    await asyncio.sleep(3)  # 模拟耗时操作
    print("{name}任务执行完毕")
    return "任务结果"

# 主协程，使用create_task并发执行任务并获取结果
async def main():
    for i in name:
        task = asyncio.create_task(task1(i))
        tasks.append(task)

    await asyncio.sleep(100)

# 运行主协程
asyncio.run(main())
