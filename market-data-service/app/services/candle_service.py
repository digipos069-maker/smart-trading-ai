from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.candle import Candle
from app.schemas.market import CandleResponse


def save_candles(
    db: Session,
    candles: list[CandleResponse],
    symbol: str,
    timeframe: str,
) -> list[Candle]:
    normalized_symbol = symbol.upper()
    normalized_timeframe = timeframe.upper()

    if not candles:
        return []

    values = [
        {
            "symbol": normalized_symbol,
            "timeframe": normalized_timeframe,
            "time": candle.time,
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "tick_volume": candle.tick_volume,
            "spread": candle.spread,
        }
        for candle in candles
    ]

    statement = insert(Candle).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=["symbol", "timeframe", "time"],
        set_={
            "open": statement.excluded.open,
            "high": statement.excluded.high,
            "low": statement.excluded.low,
            "close": statement.excluded.close,
            "tick_volume": statement.excluded.tick_volume,
            "spread": statement.excluded.spread,
        },
    )
    db.execute(statement)
    db.commit()

    return get_saved_candles(db, normalized_symbol, normalized_timeframe, len(candles))


def get_saved_candles(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 500,
) -> list[Candle]:
    statement: Select[tuple[Candle]] = (
        select(Candle)
        .where(
            Candle.symbol == symbol.upper(),
            Candle.timeframe == timeframe.upper(),
        )
        .order_by(Candle.time.desc())
        .limit(limit)
    )
    candles = list(db.scalars(statement).all())
    candles.reverse()
    return candles
