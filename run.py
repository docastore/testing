import asyncio
import uvicorn

from main import main as bot_main
from webhook import app


async def start_all():
    bot_task = asyncio.create_task(bot_main())

    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=8000)
    )
    server_task = asyncio.create_task(server.serve())

    await asyncio.gather(bot_task, server_task)


if __name__ == "__main__":
    asyncio.run(start_all())
