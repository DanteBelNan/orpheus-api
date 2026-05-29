from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String , DateTime, ForeignKey
from datetime import datetime

from app.database import Base

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=False, nullable=False) #unique false allows in the future a user to have more than one device (it is not probable, but can happen!!)
    spotify_device_id: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) 