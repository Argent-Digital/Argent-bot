from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from src.config import settings
from src.clients.user_client import ArgentCoreClient

bot = Bot(
    token= settings.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

core_client = ArgentCoreClient(base_url=settings.CORE_URL)