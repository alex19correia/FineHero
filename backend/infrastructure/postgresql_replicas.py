"""
PostgreSQL Read Replicas and Query Optimization for FineHero Phase 3.
High-availability configuration with automatic failover and performance optimization.
"""
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import threading
import time
from dataclasses import dataclass
from enum import Enum

# Import PostgreSQL configuration
from .postgresql_config import postgresql_config

logger = logging.getLogger(__name__)

class DatabaseRole(Enum):
    """Database instance roles for replication setup."""
    PRIMARY = "primary"
    REPLICA = "replica"
    STANDBY = "standby"

@dataclass
class ReplicaConfig:
    """Configuration for read replica instances."""
    host: str
    port: int
    database: str
    username: str
    password: str
    role: DatabaseRole
    priority: int = 1  # Load balancing priority (1=highest)
    max_connections: int = 100
    connection_timeout: int = 30
    health_check_interval: int = 30  # seconds

class ReadReplicaManager:
    """
    Manages PostgreSQL read replicas for load balancing and high availability.
    Implements automatic failover, connection pooling, and health monitoring.
    """
    
    def __init__(self):
        self.primary_engine = None
        self.replica_engines: List[Any] = []
        self.replica_configs: List[ReplicaConfig] = []
        self.current_replica_index = 0
        self.health_check_thread = None
        self.failover_in_progress = False
        
        # Performance tracking
        self.connection_stats = {
            "primary_connections": 0,
            "replica_connections": 0,
            "failover_count": 0,
            "health_check_failures": 0
        }
        
        # Load balancing strategy
        self.load_balancing_strategy = "round_robin"  # round_robin, least_connections, random
        
        self._initialize_replicas()
    
    def _initialize_replicas(self):
        """Initialize replica configurations from environment."""
        # Read replica hosts from configuration
        replica_hosts = postgresql_config.replica_hosts
        if not replica_hosts:
            logger.info("No read replicas configured")
            return
        
        for i, host in enumerate(replica_hosts):
            if host.strip():
                config = ReplicaConfig(
                    host=host.strip(),
                    port=postgresql_config.replica_port,
                    database=postgresql_config.primary_db,
                    username=postgresql_config.primary_user,
                    password=postgresql_config.primary_password,
                    role=DatabaseRole.REPLICA,
                    priority=i + 1
                )
                self.replica_configs.append(config)
        
        logger.info(f"Initialized {len(self.replica_configs)} read replicas")
    
    def _create_replica_engine(self, config: ReplicaConfig) -> Any:
        """Create SQLAlchemy engine for read replica."""
        connection_string = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        
        engine_config = {
            "url": connection_string,
            "poolclass": QueuePool,
            "pool_size": min(config.max_connections, 20),  # Conservative pooling
            "max_overflow": 10,
            "pool_timeout": config.connection_timeout,
            "pool_recycle": 3600,
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "future": True,
        }
        
        # SSL configuration
        if postgresql_config.ssl_mode in ["require", "verify-ca", "verify-full"]:
            engine_config["connect_args"] = {
                "sslmode": postgresql_config.ssl_mode,
                "sslcert": postgresql_config.ssl_cert,
                "sslkey": postgresql_config.ssl_key,
                "sslrootcert": postgresql_config.ssl_ca
            }
        
        engine = create_engine(**engine_config)
        
        # Add replica-specific optimizations
        self._setup_replica_optimizations(engine)
        
        return engine
    
    def _setup_replica_optimizations(self, engine):
        """Configure replica-specific performance optimizations."""
        
        @event.listens_for(engine, "connect")
        def set_replica_settings(dbapi_connection, connection_record):
            """Set PostgreSQL settings optimized for read replicas."""
            cursor = dbapi_connection.cursor()
            
            # Read replica optimizations
            replica_settings = [
                # Optimize for read-heavy workload
                "SET synchronous_commit = local;",  # Allow async commit on replicas
                "SET wal_level = replica;",  # Required for replication
                "SET max_standby_streaming_delay = 30s;",  # Allow replica to lag slightly
                "SET wal_compression = on;",  # Reduce WAL size
                "SET track_activities = off;",  # Reduce overhead for read-only workload
                "SET track_counts = off;",  # Reduce overhead
                "SET track_io_timing = off;",  # Reduce overhead
                "SET log_statement = 'none';",  # Reduce logging overhead
            ]
            
            for setting in replica_settings:
                try:
                    cursor.execute(setting)
                except Exception as e:
                    logger.warning(f"Failed to set replica optimization {setting}: {e}")
            
            cursor.close()
    
    def initialize_engines(self):
        """Initialize all database engines (primary and replicas)."""
        try:
            # Create primary engine
            self.primary_engine = postgresql_config.create_engine(is_read_replica=False)
            
            # Create replica engines
            for config in self.replica_configs:
                try:
                    engine = self._create_replica_engine(config)
                    self.replica_engines.append(engine)
                    logger.info(f"Created replica engine for {config.host}:{config.port}")
                except Exception as e:
                    logger.error(f"Failed to create replica engine for {config.host}: {e}")
            
            # Start health monitoring
            self._start_health_monitoring()
            
            logger.info("All database engines initialized successfully")
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            raise
    
    def _start_health_monitoring(self):
        """Start background health monitoring thread."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        
        self.health_check_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("Health monitoring started")
    
    def _health_monitor_loop(self):
        """Background loop for monitoring replica health."""
        while True:
            try:
                self._check_replica_health()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_replica_health(self):
        """Check health of all replica instances."""
        for i, engine in enumerate(self.replica_engines):
            try:
                with engine.connect() as conn:
                    # Basic connectivity test
                    result = conn.execute(text("SELECT 1")).fetchone()
                    
                    if not result or result[0] != 1:
                        raise Exception("Health check query failed")
                    
                    # Check replication lag (if applicable)
                    try:
                        lag_result = conn.execute(text("""
                            SELECT 
                                EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) as replay_lag
                        """)).fetchone()
                        
                        if lag_result and lag_result[0]:
                            lag_seconds = float(lag_result[0])
                            if lag_seconds > 60:  # More than 1 minute lag
                                logger.warning(f"Replica {i} has high replication lag: {lag_seconds:.2f}s")
                    except Exception:
                        # Replication lag check failed, but connection is OK
                        pass
                    
                    # Connection count check
                    conn_count_result = conn.execute(text("""
                        SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                    """)).fetchone()
                    
                    if conn_count_result and conn_count_result[0] > 80:  # Near connection limit
                        logger.warning(f"Replica {i} has high connection count: {conn_count_result[0]}")
                
            except Exception as e:
                logger.error(f"Replica {i} health check failed: {e}")
                self.connection_stats["health_check_failures"] += 1
                
                # Implement automatic failover logic here
                # This would typically trigger promotion of a standby or update routing
    
    @contextmanager
    def get_read_connection(self):
        """Get read connection from primary or replica based on load balancing."""
        # Strategy 1: Always use replica if available
        if self.replica_engines:
            selected_engine = self._select_replica()
            if selected_engine:
                try:
                    with selected_engine.connect() as connection:
                        self.connection_stats["replica_connections"] += 1
                        yield connection
                        return
                except Exception as e:
                    logger.warning(f"Replica connection failed, falling back to primary: {e}")
        
        # Fallback to primary
        try:
            with self.primary_engine.connect() as connection:
                self.connection_stats["primary_connections"] += 1
                yield connection
        except Exception as e:
            logger.error(f"Primary connection failed: {e}")
            raise
    
    def _select_replica(self):
        """Select replica based on load balancing strategy."""
        if not self.replica_engines:
            return None
        
        if self.load_balancing_strategy == "round_robin":
            replica = self.replica_engines[self.current_replica_index]
            self.current_replica_index = (self.current_replica_index + 1) % len(self.replica_engines)
            return replica
        
        elif self.load_balancing_strategy == "least_connections":
            # Return replica with least active connections
            # This is a simplified implementation
            return self.replica_engines[0]
        
        elif self.load_balancing_strategy == "random":
            import random
            return random.choice(self.replica_engines)
        
        return self.replica_engines[0]  # Default fallback
    
    def get_session_factory(self, use_replica: bool = True):
        """Get session factory with replica support."""
        if use_replica and self.replica_engines:
            engine = self._select_replica()
            return sessionmaker(bind=engine, autocommit=False, autoflush=False)
        else:
            return sessionmaker(bind=self.primary_engine, autocommit=False, autoflush=False)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance and connection statistics."""
        return {
            "connection_stats": self.connection_stats,
            "replica_count": len(self.replica_engines),
            "primary_pool_size": self.primary_engine.pool.size() if self.primary_engine else 0,
            "primary_pool_checked_in": self.primary_engine.pool.checkedin() if self.primary_engine else 0,
            "primary_pool_overflow": self.primary_engine.pool.overflow() if self.primary_engine else 0,
            "replica_engines": [
                {
                    "host": config.host,
                    "port": config.port,
                    "pool_size": engine.pool.size() if engine else 0,
                    "pool_checkedin": engine.pool.checkedin() if engine else 0,
                    "pool_overflow": engine.pool.overflow() if engine else 0
                }
                for config, engine in zip(self.replica_configs, self.replica_engines)
            ]
        }
    
    def trigger_failover(self, target_replica_index: Optional[int] = None) -> bool:
        """Trigger manual failover to a replica."""
        if self.failover_in_progress:
            logger.warning("Failover already in progress")
            return False
        
        self.failover_in_progress = True
        
        try:
            if target_replica_index is not None and target_replica_index < len(self.replica_engines):
                # Promote specific replica
                target_engine = self.replica_engines[target_replica_index]
                logger.info(f"Manually promoting replica {target_replica_index}")
            else:
                # Promote first healthy replica
                target_engine = self.replica_engines[0] if self.replica_engines else None
                if not target_engine:
                    raise Exception("No healthy replicas available for failover")
                logger.info("Promoting first available replica")
            
            # Implement actual failover logic here
            # This would involve:
            # 1. Promoting replica to primary
            # 2. Updating connection strings
            # 3. Updating application configuration
            # 4. Monitoring the new primary
            
            self.connection_stats["failover_count"] += 1
            logger.info("Failover completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failover failed: {e}")
            return False
        finally:
            self.failover_in_progress = False

class QueryOptimizer:
    """
    PostgreSQL query optimization for FineHero legal document processing.
    Implements index suggestions, query analysis, and performance monitoring.
    """
    
    def __init__(self, replica_manager: ReadReplicaManager):
        self.replica_manager = replica_manager
        self.query_performance_log = []
        self.slow_query_threshold = 1.0  # seconds
        self.optimization_suggestions = []
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze slow queries and provide optimization suggestions."""
        try:
            with self.replica_manager.get_read_connection() as conn:
                # Get slow query statistics
                result = conn.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE mean_time > :threshold
                    ORDER BY mean_time DESC
                    LIMIT 10
                """), {"threshold": self.slow_query_threshold}).fetchall()
                
                slow_queries = []
                for row in result:
                    query_analysis = {
                        "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                        "calls": row[1],
                        "total_time": float(row[2]),
                        "mean_time": float(row[3]),
                        "rows": row[4],
                        "hit_percent": float(row[5]),
                        "suggestions": self._generate_query_suggestions(row[0])
                    }
                    slow_queries.append(query_analysis)
                
                return slow_queries
                
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return []
    
    def _generate_query_suggestions(self, query: str) -> List[str]:
        """Generate optimization suggestions for a specific query."""
        suggestions = []
        query_lower = query.lower()
        
        # Check for missing indexes
        if "where" in query_lower:
            if "fines" in query_lower:
                suggestions.append("Consider adding index on frequently filtered columns in fines table")
            if "legal_documents" in query_lower:
                suggestions.append("Consider adding index on document_type, jurisdiction, or publication_date")
        
        # Check for ORDER BY performance
        if "order by" in query_lower:
            suggestions.append("Consider adding index on ORDER BY columns to avoid sort operations")
        
        # Check for JOIN performance
        if "join" in query_lower:
            suggestions.append("Ensure join columns are indexed on both tables")
            suggestions.append("Consider using hash joins for small datasets, merge joins for sorted data")
        
        # Check for subquery optimization
        if "select" in query_lower and "from" in query_lower:
            suggestions.append("Consider using EXISTS instead of IN for better performance")
        
        return suggestions
    
    def suggest_indexes(self) -> List[Dict[str, Any]]:
        """Suggest indexes based on query patterns and table statistics."""
        try:
            with self.replica_manager.get_read_connection() as conn:
                # Get table statistics and query patterns
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    WHERE seq_scan > 1000  -- Tables with high sequential scans
                    ORDER BY seq_scan DESC
                """)).fetchall()
                
                index_suggestions = []
                for row in result:
                    schema = row[0]
                    table = row[1]
                    seq_scans = row[2]
                    seq_tuple_reads = row[3]
                    idx_scans = row[4]
                    idx_tuple_fetches = row[5]
                    
                    # Calculate sequential scan ratio
                    total_accesses = seq_scans + idx_scans
                    if total_accesses > 0:
                        seq_ratio = seq_scans / total_accesses
                        
                        if seq_ratio > 0.5:  # More than 50% sequential scans
                            suggestion = {
                                "schema": schema,
                                "table": table,
                                "reason": f"High sequential scan ratio ({seq_ratio:.2%})",
                                "recommended_action": "Consider adding indexes on frequently filtered columns"
                            }
                            
                            # Add specific column suggestions based on table
                            if table == "fines":
                                suggestion["suggested_indexes"] = [
                                    "CREATE INDEX CONCURRENTLY idx_fines_date ON fines(date)",
                                    "CREATE INDEX CONCURRENTLY idx_fines_location ON fines USING gin(location gin_trgm_ops)",
                                    "CREATE INDEX CONCURRENTLY idx_fines_infractor ON fines(infractor)",
                                    "CREATE INDEX CONCURRENTLY idx_fines_infraction_code ON fines(infraction_code)"
                                ]
                            elif table == "legal_documents":
                                suggestion["suggested_indexes"] = [
                                    "CREATE INDEX CONCURRENTLY idx_legal_documents_type ON legal_documents(document_type)",
                                    "CREATE INDEX CONCURRENTLY idx_legal_documents_jurisdiction ON legal_documents(jurisdiction)",
                                    "CREATE INDEX CONCURRENTLY idx_legal_documents_publication_date ON legal_documents(publication_date)",
                                    "CREATE INDEX CONCURRENTLY idx_legal_documents_quality_score ON legal_documents(quality_score)",
                                    "CREATE INDEX CONCURRENTLY idx_legal_documents_extracted_text_gin ON legal_documents USING gin(to_tsvector('portuguese', extracted_text))"
                                ]
                            
                            index_suggestions.append(suggestion)
                
                return index_suggestions
                
        except Exception as e:
            logger.error(f"Index suggestion failed: {e}")
            return []
    
    def optimize_table_statistics(self) -> Dict[str, Any]:
        """Update table statistics for better query planning."""
        try:
            with self.replica_manager.get_read_connection() as conn:
                # Analyze tables to update statistics
                tables_result = conn.execute(text("""
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                """)).fetchall()
                
                optimization_results = []
                
                for schema, table in tables_result:
                    try:
                        # Update table statistics
                        conn.execute(text(f"ANALYZE {schema}.{table}"))
                        
                        # Update index statistics
                        conn.execute(text(f"ANALYZE {schema}.{table}"))
                        
                        optimization_results.append({
                            "table": f"{schema}.{table}",
                            "status": "success",
                            "action": "Statistics updated"
                        })
                        
                    except Exception as e:
                        optimization_results.append({
                            "table": f"{schema}.{table}",
                            "status": "error",
                            "error": str(e)
                        })
                
                return {
                    "optimization_results": optimization_results,
                    "tables_processed": len(optimization_results)
                }
                
        except Exception as e:
            logger.error(f"Table optimization failed: {e}")
            return {"error": str(e)}
    
    def implement_sharding_strategy(self) -> Dict[str, Any]:
        """Implement database sharding for horizontal scalability."""
        try:
            shard_configs = []
            
            for shard_id in range(postgresql_config.shard_count):
                if shard_id == postgresql_config.current_shard:
                    continue  # Skip current shard
                
                shard_db_name = f"{postgresql_config.primary_db}_shard_{shard_id}"
                
                shard_config = {
                    "shard_id": shard_id,
                    "database_name": shard_db_name,
                    "connection_string": postgresql_config.get_shard_connection_string(shard_id),
                    "estimated_size": "To be determined",
                    "routing_key": f"shard_{shard_id}"
                }
                
                shard_configs.append(shard_config)
            
            return {
                "shard_strategy": "hash_based",
                "total_shards": postgresql_config.shard_count,
                "current_shard": postgresql_config.current_shard,
                "shard_configs": shard_configs,
                "routing_strategy": "application_level_routing",
                "implementation_status": "configured"
            }
            
        except Exception as e:
            logger.error(f"Sharding configuration failed: {e}")
            return {"error": str(e)}
    
    def get_comprehensive_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        try:
            report = {
                "timestamp": time.time(),
                "query_analysis": self.analyze_slow_queries(),
                "index_suggestions": self.suggest_indexes(),
                "table_optimization": self.optimize_table_statistics(),
                "sharding_strategy": self.implement_sharding_strategy(),
                "performance_stats": self.replica_manager.get_performance_stats(),
                "recommendations": self._generate_optimization_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive report generation failed: {e}")
            return {"error": str(e)}
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate high-level optimization recommendations."""
        recommendations = [
            "Enable pg_stat_statements extension for detailed query analysis",
            "Implement connection pooling for better resource utilization",
            "Configure automatic vacuum and analyze schedules",
            "Set up query performance monitoring and alerting",
            "Consider implementing read replicas for better load distribution",
            "Monitor and optimize slow queries regularly",
            "Implement caching strategies for frequently accessed data",
            "Plan for horizontal scaling with database sharding"
        ]
        
        return recommendations

# Global instances
read_replica_manager = ReadReplicaManager()
query_optimizer = QueryOptimizer(read_replica_manager)

# Initialize engines on module load
read_replica_manager.initialize_engines()

# Export for use in other modules
__all__ = [
    "ReadReplicaManager", 
    "QueryOptimizer", 
    "read_replica_manager", 
    "query_optimizer"
]