from datetime import date, datetime, time, timezone

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.candle import Candle
from app.schemas.market import CandleResponse
from app.services.market_data_service import validate_symbol, validate_timeframe


def save_candles(
    db: Session,
    candles: list[CandleResponse],
    symbol: str,
    timeframe: str,
    validate_inputs: bool = True,
) -> list[Candle]:
    normalized_symbol = validate_symbol(symbol) if validate_inputs else symbol.upper()
    normalized_timeframe = validate_timeframe(timeframe) if validate_inputs else timeframe.upper()

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

    # PostgreSQL handles duplicate prevention atomically through the unique constraint.
    statement = insert(Candle).values(values)
    statement = statement.on_conflict_do_nothing(
        index_elements=["symbol", "timeframe", "time"]
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
    normalized_symbol = validate_symbol(symbol)
    normalized_timeframe = validate_timeframe(timeframe)

    statement: Select[tuple[Candle]] = (
        select(Candle)
        .where(
            Candle.symbol == normalized_symbol,
            Candle.timeframe == normalized_timeframe,
        )
        .order_by(Candle.time.desc())
        .limit(limit)
    )
    candles = list(db.scalars(statement).all())
    candles.reverse()
    return candles


def get_saved_candles_by_date_range(
    db: Session,
    symbol: str,
    timeframe: str,
    start_date: date,
    end_date: date,
) -> list[Candle]:
    normalized_symbol = validate_symbol(symbol)
    normalized_timeframe = validate_timeframe(timeframe)
    start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end_date, time.max, tzinfo=timezone.utc)

    statement: Select[tuple[Candle]] = (
        select(Candle)
        .where(
            Candle.symbol == normalized_symbol,
            Candle.timeframe == normalized_timeframe,
            Candle.time >= start_at,
            Candle.time <= end_at,
        )
        .order_by(Candle.time.asc())
    )
    return list(db.scalars(statement).all())
