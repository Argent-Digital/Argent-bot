from aiogram import Router
from src.handlers.base_handler import router as base_router
from src.handlers.key_handler import router as key_router
from src.handlers.pay_handler import router as pay_router

def get_main_router() -> Router:
    main_router = Router()

    main_router.include_router(base_router)
    main_router.include_router(key_router)
    main_router.include_router(pay_router)
    return main_router