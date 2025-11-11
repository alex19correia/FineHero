"""
Enhanced PostgreSQL Configuration for FineHero Phase 3.
Simplified approach with direct database switching.
"""
import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """
    Enhanced database configuration supporting both SQLite and PostgreSQL.
    Simple switching between databases based on environment.
    """
    
    def __init__(self):
        # Detect database type from environment
        self.database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        
        if self.database_type == "postgresql":
            self._setup_postgresql()
        else:
            self._setup_sqlite()
    
    def _setup_postgresql(self):
        """Configure PostgreSQL connection."""
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB", "finehero")
        self.username = os.getenv("POSTGRES_USER", "finehero_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "")
        
        # Connection string
        self.connection_string = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # Performance settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        
        logger.info("PostgreSQL configuration initialized")
    
    def _setup_sqlite(self):
        """Configure SQLite connection (current default)."""
        self.database_path = os.getenv("SQLITE_DB_PATH", "finehero.db")
        self.connection_string = f"sqlite:///{self.database_path}"
        
        logger.info(f"SQLite configuration initialized with database: {self.database_path}")
    
    def create_engine(self):
        """Create database engine based on current configuration."""
        if self.database_type == "postgresql":
            engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=30,
                pool_recycle=3600,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
            
            # Add PostgreSQL optimizations
            self._setup_postgresql_optimizations(engine)
        else:
            engine = create_engine(
                self.connection_string,
                connect_args={"check_same_thread": False},
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        
        return engine
    
    def _setup_postgresql_optimizations(self, engine):
        """Add PostgreSQL-specific performance optimizations."""
        
        @event.listens_for(engine, "connect")
        def set_postgres_pragma(dbapi_connection, connection_record):
            """Set PostgreSQL performance settings."""
            cursor = dbapi_connection.cursor()
            
            # Performance optimizations
            optimizations = [
                "SET synchronous_commit = on;",
                "SET work_mem = '16MB';",
                "SET effective_cache_size = '512MB';",
                "SET random_page_cost = 1.1;",
                "SET shared_buffers = '256MB';"
            ]
            
            for optimization in optimizations:
                try:
                    cursor.execute(optimization)
                except Exception as e:
                    logger.warning(f"Failed to set optimization: {e}")
            
            cursor.close()
    
    def create_session_factory(self):
        """Create session factory."""
        engine = self.create_engine()
        return sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            session_factory = self.create_session_factory()
            with session_factory() as session:
                if self.database_type == "postgresql":
                    result = session.execute("SELECT 1").fetchone()
                else:
                    result = session.execute("SELECT 1").fetchone()
                
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information for monitoring."""
        info = {
            "database_type": self.database_type,
            "connection_string": self.connection_string.replace(self.password, "***") if self.password else self.connection_string
        }
        
        if self.database_type == "postgresql":
            info.update({
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "username": self.username,
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow
            })
        else:
            info.update({
                "database_path": self.database_path
            })
        
        return info

# Global configuration instance
db_config = DatabaseConfig()

# Create engine and session factory
engine = db_config.create_engine()
SessionLocal = db_config.create_session_factory()

def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def health_check():
    """Database health check for monitoring."""
    return {
        "status": "healthy" if db_config.test_connection() else "unhealthy",
        "database_type": db_config.database_type,
        "info": db_config.get_database_info()
    }