from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert
from src.database.database import async_session_factory
from src.database.models import UsersOrm

class UserDao:

    @classmethod
    async def add_user(cls, user_id: int, username: str, first_name: str, refferer_id: int | None = None):
        async with async_session_factory() as session:
            stmt = insert(UsersOrm).values(
                user_id = user_id,
                username = username,
                first_name = first_name,
                refferer_id = refferer_id,
                balance = 30
            ).on_conflict_do_update(
                index_elements=['user_id'],
                set_={
                    'username': username,
                    'first_name': first_name
                }
            )

            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_user_balance(cls, user_id: int) -> int | None:
        async with async_session_factory() as session:
            query = select(UsersOrm.balance).where(UsersOrm.user_id == user_id)
            result = await session.execute(query)
            return result.scalar()
        
    @classmethod
    async def update_balance(cls, user_id: int, amount: int):
        async with async_session_factory() as session:
            stmt = {
                update(UsersOrm)
                .where(UsersOrm.user_id == user_id)
                .values(balance = UsersOrm.balance + amount)
            }
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_all_active_users(cls) -> list[UsersOrm]:
        async with async_session_factory() as session:
            query = (
                select(UsersOrm)
                .join(UsersOrm.key)
            )
            res = await session.execute(query)
            return res.scalars().unique().all()
        
    @classmethod
    async def get_all_user_ids(cls) -> list[int]:
        async with async_session_factory() as session:
            query = (
                select(UsersOrm.user_id)
            )
            res = await session.execute(query)
            return res.scalars().unique().all()
        
    @classmethod
    async def get_referrer(cls, user_id: int) -> int | None:
        async with async_session_factory() as session:
            query = (
                select(UsersOrm.referrer_id)
                .where(UsersOrm.user_id == user_id)
            )
            res = await session.execute(query)
            return res.scalar()