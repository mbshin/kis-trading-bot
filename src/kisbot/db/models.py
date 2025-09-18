from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Float, Text, DateTime, Integer, JSON
from datetime import datetime
from .base import Base

class Signal(Base):
    __tablename__ = 'signals'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime]
    symbol: Mapped[str] = mapped_column(Text)
    side: Mapped[str] = mapped_column(Text)
    k: Mapped[float] = mapped_column(Float)
    d: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime]
    clordid: Mapped[str] = mapped_column(Text, unique=True)
    symbol: Mapped[str]
    side: Mapped[str]
    qty: Mapped[int] = mapped_column(Integer)
    type: Mapped[str]
    px: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str]
    mode: Mapped[str]

class Trade(Base):
    __tablename__ = 'trades'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(BigInteger)
    ts: Mapped[datetime]
    symbol: Mapped[str]
    side: Mapped[str]
    qty: Mapped[int]
    px: Mapped[float]

class Position(Base):
    __tablename__ = 'positions'
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    qty: Mapped[int] = mapped_column(Integer)
    avg_px: Mapped[float] = mapped_column(Float)
    u_pnl: Mapped[float] = mapped_column(Float)
    r_pnl: Mapped[float] = mapped_column(Float)
    last_ts: Mapped[datetime | None]

class PnLDaily(Base):
    __tablename__ = 'pnl_daily'
    dt: Mapped[datetime] = mapped_column(primary_key=True)
    realized: Mapped[float] = mapped_column(Float)
    unrealized: Mapped[float] = mapped_column(Float)
    max_dd: Mapped[float] = mapped_column(Float)

class BacktestRun(Base):
    __tablename__ = 'bt_runs'
    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    started: Mapped[datetime | None]
    finished: Mapped[datetime | None]
    params: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
