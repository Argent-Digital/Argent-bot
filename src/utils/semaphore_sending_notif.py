import asyncio

from aiogram import Bot

semaphore = asyncio.Semaphore(20)


async def send_with_semaphore(user_id: int, text_func: str, bot: Bot):
    async with semaphore:
        try:
            await bot.send_message(
                    chat_id=user_id,
                    text=text_func,
                    parse_mode="html"
                )
        except Exception as e:
            print(f"Error sending to user {user_id}: {e}")
