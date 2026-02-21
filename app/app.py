from fastapi import FastAPI, HTTPException, Form, Depends, status
from app.db import create_db_tables, get_async_session, Tweet, Like
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from uuid import UUID, uuid4
from app.schemas import UserRead, UserCreate, UserUpdate, TweetPostRequest, TweetResponse, TweetPatchRequest
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
        tweet: TweetPostRequest,
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

@app.get('/tweets', status_code=status.HTTP_200_OK)
async def get_tweets(user: User = Depends(current_active_user),
                    session: AsyncSession = Depends(get_async_session)) -> list[TweetResponse]:
    result = await session.execute(select(Tweet).order_by(Tweet.created_at.desc()))
    tweets = [row[0] for row in result.all()]

    result = await session.execute(select(User))

    return tweets

@app.get('/tweets/{tweet_id}', status_code = status.HTTP_202_ACCEPTED)
async def get_tweet(tweet_id: UUID,
                    session: AsyncSession = Depends(get_async_session)) -> TweetResponse:
    result = await session.execute(select(Tweet).filter_by(id=tweet_id))
    tweet_obj = result.scalars().first()

    if tweet_obj is None:
        raise HTTPException(status_code=404, detail='Tweet not found... ')

    return tweet_obj

@app.patch('/tweets/{tweet_id}', status_code=status.HTTP_202_ACCEPTED)
async def patch_tweet(tweet_id: UUID, tweet: TweetPatchRequest, user: User = Depends(current_active_user),
                session: AsyncSession = Depends(get_async_session)) -> TweetResponse:
    
    result = await session.execute(select(Tweet).filter_by(id=tweet_id))
    tweet_obj = result.scalars().first()

    if tweet_obj is None:
        raise HTTPException(status_code=404, detail='Tweet not found... ')

    for name, value in tweet.model_dump().items():
        if value  is not None:
            setattr(tweet_obj, name, value)
    
    await session.commit()
    await session.refresh(tweet_obj)

    return tweet_obj

@app.delete('/tweets/{tweet_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_tweet(tweet_id: UUID,
                       session: AsyncSession = Depends(get_async_session),
                       user: User = Depends(current_active_user)):
    result = await session.execute(select(Tweet).filter_by(id=tweet_id))
    tweet_obj = result.scalars().first()

    if not tweet_obj:
        raise HTTPException(status_code=404, detail='Tweet not found... ')
    
    await session.delete(tweet_obj)
    await session.commit()
    
    return tweet_obj

@app.post('/tweets/{tweet_id}/like', status_code=status.HTTP_201_CREATED)
async def like_tweet(tweet_id: UUID,
               session: AsyncSession = Depends(get_async_session),
               user: User = Depends(current_active_user)):
    
    like_obj = Like(
        tweet_id = tweet_id
    )
    session.add(like_obj)
    await session.commit()
    await session.refresh(like_obj)

    return {'message': 'Tweet liked... '}

@app.delete('/tweets/{tweet_id}/dislike', status_code=status.HTTP_202_ACCEPTED)
async def dislike_tweet(tweet_id: UUID,
                        session: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_active_user)):
    
    result = await session.execute(select(Like).where(Like.tweet_id == tweet_id))
    like = result.scalars().first()

    if not like:
        raise HTTPException(status_code=404, detail='Like of a tweet not found... ')
    
    await session.delete(like)
    await session.commit()
    
    return {'message': 'Like deleted... '}
