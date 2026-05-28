from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from datetime import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    spotify_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    spotify_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    spotify_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) 
