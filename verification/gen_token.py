import asyncio
from Grabber.webapp.auth import create_session

async def main():
    user = {"id": 12345678, "first_name": "Test User", "balance": 1000}
    res = await create_session(user)
    if res:
        token, user_id = res
        print(f"TOKEN:{token}")
    else:
        print("Failed to create session")

if __name__ == "__main__":
    asyncio.run(main())
