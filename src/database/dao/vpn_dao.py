from sqlalchemy import insert, select, UUID, delete
from sqlalchemy.dialects.postgresql import insert
import uuid
from src.database.database import async_session_factory
from src.database.models import VpnKeysOrm

class VpnKeyDao:

    @classmethod
    async def add_vpn_key(
        cls, 
        user_id: int,
        server_key_id: str,
        key_name: str,
        access_url: str,
        protocol: str = "outline",
        vless_uuid: uuid.UUID | None = None
    ):
        async with async_session_factory() as session:
            stmt = (
                insert(VpnKeysOrm)
                .values(
                    user_id = user_id,
                    server_key_id = server_key_id,
                    key_name = key_name,
                    access_url = access_url, 
                    protocol = protocol,
                    vless_uuid = vless_uuid
                )
                .on_conflict_do_update(
                    index_elements=['user_id'],
                    set_={
                        'server_key_id': server_key_id,
                        'key_name': key_name,
                        'access_url': access_url,
                        "protocol": protocol,
                        "vless_uuid": vless_uuid
                    }
                )
            )

            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_user_access_url(cls, user_id: int):
        async with async_session_factory() as session:
            stmt = (
                select(VpnKeysOrm.access_url)
                .where(VpnKeysOrm.user_id == user_id)
            )
            res = await session.execute(stmt)
            return res.scalar()

    @classmethod
    async def get_user_vpn_data(cls, user_id: int):
        async with async_session_factory() as session:
            stmt = (
                select(VpnKeysOrm)
                .where(VpnKeysOrm.user_id == user_id)
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()
        
    @classmethod
    async def get_all_vpn_keys(cls) -> list[VpnKeysOrm]:
        async with async_session_factory() as session:
            stmt = (
                select(VpnKeysOrm)
            )
            res = await session.execute(stmt)
            return res.scalars().all()
        
    @classmethod 
    async def delete_vpn_key(cls, user_id: int):
        async with async_session_factory() as session:
            stmt = (
                delete(VpnKeysOrm)
                .where(VpnKeysOrm.user_id == user_id)
            )
            await session.execute(stmt)
            await session.commit()