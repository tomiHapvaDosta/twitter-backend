from fastapi import FastAPI, HTTPException, Form, Depends, status
from app.db import create_db_tables, get_async_session, Tweet, Like
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from uuid import UUID, uuid4
from app.schemas import UserRead, UserCreate, UserUpdate, TweetCreate, TweetResponse
from app.users import auth_backend, current_active_user, fastapi_users, User


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix='/auth/jwt', tags=['auth'])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix='/auth', tags=['auth'])
app.include_router(fastapi_users.get_reset_password_router(), prefix='/auth', tags=['auth'])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix='/auth', tags=['auth'])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix='/auth', tags=['users'])

@app.post('/tweets', status_code=status.HTTP_201_CREATED)
async def post_tweet(
        tweet: TweetCreate,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)) -> TweetResponse:
    
    tweet_obj = Tweet(
        user_id = user.id,
        content = tweet.content,
        title = tweet.title
    )

    session.add(tweet_obj)
    await session.commit()
    await session.refresh(tweet_obj)

    return TweetResponse(
        id=tweet_obj.id,
        user_id=tweet_obj.user_id,
        title=tweet_obj.title,
        content=tweet_obj.content,
        created_at=tweet_obj.created_at,
        email=user.email
    )

@app.get('/tweets')
async def get_tweets(user: User = Depends(current_active_user),
                    session: AsyncSession = Depends(get_async_session)) -> list[TweetResponse]:
    result = await session.execute(select(Tweet).order_by(Tweet.created_at.desc()))
    tweets = [row[0] for row in result.all()]

    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]
    user_dict = {u.id : u.email for u in users}

    return [
        TweetResponse(
            id=tweet.id,
            user_id=tweet.user_id,
            title=tweet.title,
            content=tweet.content,
            created_at=tweet.created_at,
            email=user_dict.get(tweet.user_id, 'Unknown user')
        )
        for tweet in tweets
    ]
