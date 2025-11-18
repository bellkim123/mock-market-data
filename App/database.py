# App/database.py

from __future__ import annotations

import os


from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# .env 로부터 환경변수 로딩
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다. (.env 확인 필요)")

# MySQL/MariaDB용 엔진
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Session:
    """
    FastAPI DI에서 사용할 DB 세션 의존성
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
