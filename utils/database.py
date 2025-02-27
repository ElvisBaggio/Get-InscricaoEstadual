from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create the database file in the project root
SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'ie_lookups.db')}"

# Create engine
engine = create_engine(SQLITE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class IELookup(Base):
    __tablename__ = "ie_lookups"

    cnpj = Column(String(14), primary_key=True)
    ie_number = Column(String(20))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    request_count = Column(Integer, default=1)
    last_success = Column(Boolean)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "cnpj": self.cnpj,
            "ie_number": self.ie_number,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "request_count": self.request_count,
            "last_success": self.last_success,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
