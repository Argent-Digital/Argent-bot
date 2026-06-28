import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from src.schemas.bot_schema import DistResponse
from src.config import settings

async def run_distribution(bot: Bot, user_ids: list[int], post_text: str):
    count = 0
    count_banned = 0
    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id, 
                text=post_text, 
                parse_mode="HTML"
            )
            count += 1
            await asyncio.sleep(0.05) 
            
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await bot.send_message(chat_id=user_id, text=post_text, parse_mode="HTML")
            count += 1
            
        except TelegramForbiddenError:
            count_banned += 1
            continue
        except Exception:
            continue

    await bot.send_message(
        chat_id=settings.TG_ADM_ID,
        text=f"Результаты рассылки:\nУспешно({count})\nВ бане у {count_banned} юзеров!"
    )

    return DistResponse(count=count, count_banned=count_banned)