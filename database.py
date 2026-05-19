from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

SessionLocal = (
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    if engine
    else None
)

Base = declarative_base()


def get_db():
    if SessionLocal is None:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL nao configurada no ambiente do servidor",
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
