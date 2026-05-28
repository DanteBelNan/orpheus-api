from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=True) #Se loguean querys, en caso productivo habria que darlo de baja

ASyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False #Se le asigna esto para evitar que de problemas al tener persistir datos sin recargar
)

class Base(DeclarativeBase): #Se va a encargar de hacer de clase que mapee nuestros modelos en tablas de sql
    pass

async def get_db(): #Va a ser quien le de el contexto async de la db a los services
    async with ASyncSessionLocal() as session:
        yield session 