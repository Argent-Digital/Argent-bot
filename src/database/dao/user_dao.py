from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert
from src.database.database import async_session_factory
from src.database.models import UsersOrm

