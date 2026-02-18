"""Database connection and session management."""

import ssl
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# SSL 설정 (Azure MySQL 필수)
# DATABASE_URL에서 ssl 관련 파라미터 제거하고 connect_args로 전달
connect_args = {}
if "azure" in settings.DATABASE_URL.lower() or "ssafy" in settings.DATABASE_URL.lower():
    # Azure MySQL은 SSL 필수 - 인증서 검증 없이 SSL 활성화
    connect_args["ssl"] = {
        "ssl": True,
        "ssl_verify_cert": False,
        "ssl_verify_identity": False,
    }

# URL에서 ssl 관련 쿼리 파라미터 제거
db_url = settings.DATABASE_URL
for param in ["ssl_mode=", "ssl_verify_cert=", "ssl_verify_identity=", "ssl="]:
    if param in db_url:
        # 파라미터 제거
        import re
        db_url = re.sub(rf'&?{re.escape(param)}[^&]*', '', db_url)
        db_url = db_url.replace('?&', '?').rstrip('&').rstrip('?')

# Create SQLAlchemy engine
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    connect_args=connect_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
