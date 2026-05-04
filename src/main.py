from fastapi import FastAPI
from src.loader_bot import bot, dp, core_client
from src.api.pay_api import router as pay_router
from src.handlers.user_handlers import router as user_router 
import uvicorn

app = FastAPI()

app.state.bot = bot

# Подключаем роутеры
app.include_router(pay_router)
dp.include_router(user_router)

async def start_bot():
    await dp.start_polling(bot, core_client=core_client)
