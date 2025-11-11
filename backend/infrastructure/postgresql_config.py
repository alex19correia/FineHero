
"""
PostgreSQL/PostGIS production configuration for FineHero Phase 3.
Enterprise-grade database setup with connection pooling, replication, and sharding.
"""
import os
import ssl
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqla
lchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class PostgreSQLConfig:
    """
    Production PostgreSQL configuration with PostGIS support.
    Handles connection pooling, replication, and performance optimization.
    """
    
    def __init__(self):
        # Database connection settings
        self.primary_host = os.getenv("POSTGRES_PRIMARY_HOST", "localhost")
        self.primary_port = int(os.getenv("POSTGRES_PRIMARY_PORT", "5432"))
        self.primary_db = os.getenv("POSTGRES_DB", "finehero_prod")
        self.primary_user = os.getenv("POSTGRES_USER", "finehero_user")
        self.primary_password = os.getenv("POSTGRES_PASSWORD")
        
        # Read replica settings
        self.replica_hosts = os.getenv("POSTGRES_REPLICA_HOSTS", "").split(",") if os.getenv("POSTGRES_REPLICA_HOSTS") else []
        self.replica_port = int(os.getenv("POSTGRES_REPLICA_PORT", "5432"))
        
        # Connection pooling configuration
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
        # SSL configuration
        self.ssl_mode = os.getenv("DB_SSL_MODE", "require")
        self.ssl_cert = os.getenv("DB_SSL_CERT")
        self.ssl_key = os.getenv("DB_SSL_KEY")
        self.ssl_ca = os.getenv("DB_SSL_CA")
        
        # Performance settings
        self.enable_postgis = os.getenv("ENABLE_POSTGIS", "true").lower() == "true"
        self.query_cache_size = int(os.getenv("QUERY_CACHE_SIZE", "128"))
        self.shared_buffers = os.getenv("SHARED_BUFFERS", "256MB")
        
        # Sharding configuration
        self.shard_count = int(os.getenv("SHARD_COUNT", "4"))
        self.current_shard = int(os.getenv("CURRENT_SHARD", "0"))
        
        # Backup configuration
        self.backup_retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        self.wal_archive_enabled = os.getenv("WAL_ARCHIVE_ENABLED", "true").lower() == "true"
        
    @property
    def primary_connection_string(self) -> str:
        """Generate primary database connection string."""
        return f"postgresql://{self.primary_user}:{self.primary_password}@{self.primary_host}:{self.primary_port}/{self.primary_db}"
    
    @property
    def async_connection_string(self) -> str:
        """Generate async database connection string."""
        return f"postgresql+asyncpg://{self.primary_user}:{self.primary_password}@{self.primary_host}:{self.primary_port}/{self.primary_db}"
    
    @property
    def replica_connection_strings(self) -> list[str]:
        """Generate replica connection strings for load balancing."""
        if not self.replica_hosts:
            return [self.primary_connection_string]
        
        replicas = []
        for host in self.replica_hosts:
            if host.strip():
                replicas.append(
                    f"postgresql://{self.primary_user}:{self.primary_password}@{host.strip()}:{self.replica_port}/{self.primary_db}"
                )
        return replicas if replicas else [self.primary_connection_string]
    
    def get_engine_config(self, is_read_replica: bool = False) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration for production deployment."""
        
        # Connection string for read replica or primary
        connection_string = self.replica_connection_strings[0] if is_read_replica else self.primary_connection_string
        
        # Base engine configuration
        config = {
            "url": connection_string,
            "poolclass": QueuePool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "future": True,
        }
        
        # SSL configuration
        if self.ssl_mode in ["require", "verify-ca", "verify-full"]:
            ssl_context = ssl.create_default_context()
            if self.ssl_ca:
                ssl_context.load_verify_locations(self.ssl_ca)
            if self.ssl_cert and self.ssl_key:
                ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
            
            config["connect_args"] = {
                "sslmode": self.ssl_mode,
                "sslcert": self.ssl_cert,
                "sslkey": self.ssl_key,
                "sslrootcert": self.ssl_ca
            }
        
        # PostGIS-specific settings
        if self.enable_postgis:
            config["connect_args"]["options"] = "-c search_path=public,postgis"
        
        return config
    
    def create_engine(self, is_read_replica: bool = False):
        """Create SQLAlchemy engine with production optimizations."""
        config = self.get_engine_config(is_read_replica)
        
        engine = create_engine(**config)
        
        # Add performance monitoring
        self._setup_performance_monitoring(engine)
        
        return engine
    
    def create_async_engine(self):
        """Create async SQLAlchemy engine for high-concurrency workloads."""
        config = self.get_engine_config()
        config["url"] = self.async_connection_string
        
        engine = create_async_engine(**config)
        self._setup_performance_monitoring(engine.sync_engine)
        
        return engine
    
    def _setup_performance_monitoring(self, engine):
        """Add performance monitoring and query optimization."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries for optimization."""
            if hasattr(context, 'query_start_time'):
                return
            
            context._query_start_time = __import__('time').time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Monitor query performance and log slow queries."""
            if hasattr(context, '_query_start_time'):
                query_time = __import__('time').time() - context._query_start_time
                
                # Log queries that take longer than 100ms
                if query_time > 0.1:
                    logger.warning(f"Slow query detected ({query_time:.3f}s): {statement[:100]}...")
                
                # Performance metrics could be sent to monitoring system here
        
        # Set PostgreSQL-specific optimizations
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set PostgreSQL performance optimizations."""
            if hasattr(dbapi_connection, 'cursor'):
                cursor = dbapi_connection.cursor()
                
                # Connection and query optimizations
                optimizations = [
                    # Set synchronous commit for balance between durability and performance
                    "SET synchronous_commit = on;",
                    # Enable query planner to use more memory for planning
                    "SET work_mem = '16MB';",
                    # Set effective cache size to help planner make better decisions
                    "SET effective_cache_size = '512MB';",
                    # Enable parallel query processing
                    "SET max_parallel_workers_per_gather = 4;",
                    # Set random page cost for better query planning
                    "SET random_page_cost = 1.1;",
                ]
                
                for optimization in optimizations:
                    try:
                        cursor.execute(optimization)
                    except Exception as e:
                        logger.warning(f"Failed to set optimization {optimization}: {e}")
                
                cursor.close()
    
    def get_session_factory(self, is_read_replica: bool = False) -> sessionmaker:
        """Create session factory with optimized configuration."""
        engine = self.create_engine(is_read_replica)
        
        return sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    
    def get_async_session_factory(self) -> sessionmaker:
        """Create async session factory."""
        engine = self.create_async_engine()
        
        return sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    
    @contextmanager
    def get_connection_pool(self, is_read_replica: bool = False):
        """Context manager for database connection pooling."""
        session_factory = self.get_session_factory(is_read_replica)
        
        with session_factory() as session:
            try:
                yield session
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
    
    def get_shard_connection_string(self, shard_id: int) -> str:
        """Get connection string for specific database shard."""
        if self.shard_count <= 1:
            return self.primary_connection_string
        
        # Simple sharding strategy - append shard number to database name
        shard_db = f"{self.primary_db}_shard_{shard_id}"
        
        return f"postgresql://{self.primary_user}:{self.primary_password}@{self.primary_host}:{self.primary_port}/{shard_db}"
    
    def get_read_replica_connection(self) -> str:
        """Get a read replica connection string for load balancing."""
        import random
        
        if not self.replica_hosts:
            return self.primary_connection_string
        
        # Round-robin selection of read replicas
        return random.choice(self.replica_connection_strings)
    
    def validate_connection(self) -> bool:
        """Validate database connection and PostGIS availability."""
        try:
            with self.get_connection_pool() as session:
                # Test basic connection
                result = session.execute("SELECT 1").fetchone()
                if not result or result[0] != 1:
                    return False
                
                # Test PostGIS if enabled
                if self.enable_postgis:
                    postgis_version = session.execute("SELECT PostGIS_Version()").fetchone()
                    logger.info(f"PostGIS version: {postgis_version[0] if postgis_version else 'Not available'}")
                
                # Test connection pool
                pool_status = session.execute("""
                    SELECT 
                        count(*) as active_connections,
                        state
                    FROM pg_stat_activity 
                    WHERE datname = %s
                    GROUP BY state
                """, (self.primary_db,)).fetchall()
                
                logger.info(f"Database connection pool status: {pool_status}")
                
                return True
                
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            return False

# Global configuration instance
postgresql_config = PostgreSQLConfig()

# Optimized database engine for primary database
primary_engine = postgresql_config.create_engine(is_read_replica=False)

# Optimized database engine for read replicas
read_replica_engine = postgresql_config.create_engine(is_read_replica=True)

# Session factories
PrimarySessionLocal = postgresql_config.get_session_factory(is_read_replica=False)
ReadReplicaSessionLocal = postgresql_config.get_session_factory(is_read_replica=True)

# Async session factory
AsyncSessionLocal = postgresql_config.get_async_session_factory()

# Performance-optimized connection pool contexts
@contextmanager
def get_db_session(is_read_replica: bool = False):
    """Get database session with optimized connection handling."""
    if is_read_replica:
        with ReadReplicaSessionLocal() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Read replica session error: {e}")
                session.rollback()
                raise
            finally:
                session.close()
    else:
        with PrimarySessionLocal() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Primary session error: {e}")
                session.rollback()
                raise
            finally:
                session.close()

@contextmanager
def get_async_db_session():
    """Get async database session for high-concurrency operations."""
    with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async session error: {e}")
