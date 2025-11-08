"""
Database configuration and session management
"""
from sqlmodel import SQLModel, create_engine, Session

# SQLite database URL (can be changed to PostgreSQL for production)
DATABASE_URL = "sqlite:///./store.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


