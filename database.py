"""
Database layer for Backtester - PostgreSQL with SQLAlchemy
Migration from SQLite to PostgreSQL
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://backtester:changeme@localhost:5432/backtester'
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Scoped session for thread safety
ScopedSession = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()


# ============================================================================
# Models (matching init-db.sql backtester schema)
# ============================================================================

class StrategyConfig(Base):
    """Strategy configuration model"""
    __tablename__ = 'strategy_configs'
    __table_args__ = {'schema': 'backtester'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    config_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = Column(Boolean, default=False)
    author = Column(String(100), default='user')
    tags = Column(JSON)  # Using JSON instead of ARRAY for SQLAlchemy compatibility
    performance_score = Column(Float, default=0.0)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config_json': self.config_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_public': self.is_public,
            'author': self.author,
            'tags': self.tags,
            'performance_score': self.performance_score
        }


class BacktestHistory(Base):
    """Backtest history model"""
    __tablename__ = 'backtest_history'
    __table_args__ = {'schema': 'backtester'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), unique=True, nullable=False)  # UUID as string
    symbol = Column(String(50))
    timeframe = Column(String(10))
    config_name = Column(String(255))
    config_json = Column(JSON, nullable=False)
    results_json = Column(JSON)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    order_type = Column(String(10), default='long')
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'config_name': self.config_name,
            'config_json': self.config_json,
            'results_json': self.results_json,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'order_type': self.order_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }


# ============================================================================
# Database utilities
# ============================================================================

@contextmanager
def get_db_session():
    """
    Context manager for database sessions

    Usage:
        with get_db_session() as session:
            result = session.query(StrategyConfig).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def get_db():
    """
    Dependency for FastAPI/Flask routes

    Usage (FastAPI):
        @app.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """
    Initialize database tables
    NOTE: Tables are created via init-db.sql on first startup
    This function is for verification/migrations only
    """
    try:
        # Test connection
        with engine.connect() as conn:
            logger.info("✓ Database connection successful")

        # Create tables if they don't exist (backup)
        # Base.metadata.create_all(bind=engine)
        # logger.info("✓ Database tables verified")

        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def check_db_health():
    """Check database health"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "postgresql"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# Helper functions for common operations
# ============================================================================

def save_strategy_config(name: str, config: dict, description: str = "",
                        is_public: bool = False, author: str = "user", tags: list = None):
    """Save or update strategy configuration"""
    with get_db_session() as session:
        # Check if exists
        existing = session.query(StrategyConfig).filter_by(name=name).first()

        if existing:
            # Update
            existing.description = description
            existing.config_json = config
            existing.is_public = is_public
            existing.author = author
            existing.tags = tags or []
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated strategy config: {name}")
        else:
            # Create new
            new_config = StrategyConfig(
                name=name,
                description=description,
                config_json=config,
                is_public=is_public,
                author=author,
                tags=tags or []
            )
            session.add(new_config)
            logger.info(f"Created strategy config: {name}")

        session.commit()


def save_backtest_result(task_id: str, config: dict, results: dict = None, status: str = "completed"):
    """Save backtest result"""
    with get_db_session() as session:
        # Extract metadata
        symbol = config.get('symbol', 'Unknown')
        timeframe = config.get('timeframe', 'Unknown')

        # Extract metrics from results
        if results:
            basic_stats = results.get('basic_stats', {})
            total_return = basic_stats.get('total_return', 0.0)
            total_trades = basic_stats.get('total_trades', 0)
            win_rate = basic_stats.get('win_rate', 0.0)
            max_drawdown = results.get('drawdown_stats', {}).get('max_drawdown', 0.0)
            sharpe_ratio = results.get('risk_metrics', {}).get('sharpe_ratio', 0.0)
        else:
            total_return = total_trades = win_rate = max_drawdown = sharpe_ratio = 0.0

        backtest = BacktestHistory(
            task_id=task_id,
            symbol=symbol,
            timeframe=timeframe,
            config_name=f"{symbol}_{timeframe}",
            config_json=config,
            results_json=results,
            status=status,
            total_trades=total_trades,
            win_rate=win_rate,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            order_type=config.get('order_type', 'long'),
            start_date=config.get('start_date'),
            end_date=config.get('end_date'),
            completed_at=datetime.utcnow() if status == 'completed' else None
        )

        session.add(backtest)
        session.commit()
        logger.info(f"Saved backtest result: {task_id}")


def get_backtest_by_task_id(task_id: str):
    """Get backtest by task ID"""
    with get_db_session() as session:
        backtest = session.query(BacktestHistory).filter_by(task_id=task_id).first()
        return backtest.to_dict() if backtest else None


def get_recent_backtests(limit: int = 50):
    """Get recent backtests"""
    with get_db_session() as session:
        backtests = session.query(BacktestHistory)\
            .order_by(BacktestHistory.created_at.desc())\
            .limit(limit)\
            .all()
        return [b.to_dict() for b in backtests]


def get_all_strategy_configs():
    """Get all strategy configurations"""
    with get_db_session() as session:
        configs = session.query(StrategyConfig)\
            .order_by(StrategyConfig.updated_at.desc())\
            .all()
        return [c.to_dict() for c in configs]


# ============================================================================
# Initialization on import
# ============================================================================

if __name__ != "__main__":
    logger.info("Initializing database connection...")
    init_database()
