from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String , DateTime, ForeignKey, Text
from datetime import datetime

from app.database import Base

class Vinyl(Base):
    __tablename__ = "vinyls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=False, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) 
    #Last 3 populates when we assign the album
    spotify_uri: Mapped[str] = mapped_column(String(255), nullable=True)
    album_name: Mapped[str] =  mapped_column(String(255), nullable=True)
    album_art_url: Mapped[str] =  mapped_column(Text, nullable=True)
    #Last one will be rewritten each time we play the vinyl
    last_played: Mapped[datetime] = mapped_column(DateTime, nullable=True)