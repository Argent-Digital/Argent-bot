from sqlalchemy import Table, Column, Integer, String, ForeignKey, text, BigInteger, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.database import Base
from typing import Optional, Annotated
import uuid
import datetime

intpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]

class UsersOrm(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None]
    first_name: Mapped[str]
    balance: Mapped[int] = mapped_column(server_default="0")
    referrer_id: Mapped[int | None] = mapped_column(BigInteger)
    registration_date: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )
    is_verified: Mapped[bool] = mapped_column(server_default=text("false"))

    key: Mapped["VpnKeysOrm"] = relationship(back_populates="user", uselist=False)

class VpnKeysOrm(Base):
    __tablename__ = "vpn_keys"

    key_id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    server_key_id: Mapped[str | None]
    key_name: Mapped[str]
    access_url: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    protocol: Mapped[str] = mapped_column(server_default=text("outline"))
    vless_uuid: Mapped[uuid.UUID] = mapped_column(UUID)

    user: Mapped["UsersOrm"] = relationship(back_populates="key")