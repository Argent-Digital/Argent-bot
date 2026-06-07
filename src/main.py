from fastapi import FastAPI
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from src.loader_bot import bot, dp, core_client
from src.api.pay_api import router as pay_router
from src.handlers.init_handler import get_main_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("starting Argent bot")

    if not dp.sub_routers:
        dp.include_router(get_main_router())

    polling_tasks = asyncio.create_task(
        dp.start_polling(bot, core_client=core_client)
    )

    yield

    print("stopping Argent bot")
    await core_client.close()
    print("client closing")

    polling_tasks.cancel()
    try:
        await polling_tasks
    except asyncio.CancelledError:
        print("Фоновый полинг успешно остановлен.")

app = FastAPI(
    title="Argent bot API",
    description="Telegram bot",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.bot = bot

app.include_router(pay_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) #8002 in container