from app.database.session import Base, engine
from app.models import Candle  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
