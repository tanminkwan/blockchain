import asyncio

async def print_with_delay(message, delay):
    print(f"Waiting for {delay} seconds...")
    await asyncio.sleep(delay)  # delay 동안 일시 중지, 다른 작업이 실행 가능
    print(message)

async def main():
    # 두 작업을 동시에 실행
    await asyncio.gather(
        print_with_delay("Hello after 5 seconds!", 5),
        print_with_delay("Hello after 1 second!", 1)
    )
    print("Done!")

asyncio.run(main())
