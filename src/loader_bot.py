from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from src.config import settings
from src.clients.core_client import ArgentCoreClient
from src.clients.pay_client import ArgentPayClient

bot = Bot(
    token= settings.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

core_client = ArgentCoreClient(base_url=settings.CORE_URL)

pay_client = ArgentPayClient(base_url=settings.PAY_URL)