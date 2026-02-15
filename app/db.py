from collections.abc import AsyncGenerator
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends

DATABASE_URL = 'sqlite+aiosqlite:///./test.db'

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    username = Column(Text, unique=True, nullable=False)
    tweets = relationship('Tweet', back_populates='user')
    
    tweets = relationship('Tweet', back_populates='user')
    

class Tweet(Base):
    __tablename__ = 'tweets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    title = Column(Text, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='tweets')
    
    
class Like(Base):
    __tablename__ = 'likes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tweet_id = Column(UUID(as_uuid=True), ForeignKey('tweets.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tweet = relationship('Tweet')

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)