from app.database.session import Base, engine

# Import models so SQLAlchemy registers their metadata before create_all().
from app.models import AIAnalysis, BacktestResult, Candle, ICTSignal, NewsEvent  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
