"""
Simple Performance Monitoring and Health Check System for FineHero Phase 3.
Provides basic metrics, health monitoring, and performance optimization.
"""
import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
import threading
import os
from dataclasses import dataclass, field
from collections import deque, defaultdict

# Import our database and caching systems
from ..database_enhanced import db_config, health_check as db_health_check
from .redis_cache import cache

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics storage."""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime = field(default_factory=datetime.now)
    database_time: Optional[float] = None
    cache_hit: Optional[bool] = None

@dataclass
class SystemHealth:
    """System health status."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    database_status: str
    redis_status: str
    active_connections: int
    errors: List[str] = field(default_factory=list)

class PerformanceMonitor:
    """
    Simple performance monitoring system for FineHero.
    Tracks API response times, database performance, and system health.
    """
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.endpoint_stats = defaultdict(list)
        self.slow_requests = []
        self.threshold_warning = 2.0  # seconds
        self.threshold_critical = 5.0  # seconds
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Start background monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background system monitoring."""
        self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def _monitor_system(self):
        """Background system monitoring loop."""
        while True:
            try:
                self._collect_system_metrics()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect basic system metrics."""
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Log system warnings
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                logger.warning(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                logger.warning(f"High disk usage: {disk.percent}%")
                
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    def record_request(self, endpoint: str, method: str, response_time: float, 
                      status_code: int, database_time: Optional[float] = None,
                      cache_hit: Optional[bool] = None):
        """Record a request for performance tracking."""
        with self._lock:
            metric = PerformanceMetrics(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                database_time=database_time,
                cache_hit=cache_hit
            )
            
            self.metrics.append(metric)
            
            # Track slow requests
            if response_time > self.threshold_warning:
                self.slow_requests.append({
                    'timestamp': datetime.now(),
                    'endpoint': endpoint,
                    'response_time': response_time,
                    'status_code': status_code
                })
                
                # Keep only recent slow requests (last 100)
                if len(self.slow_requests) > 100:
                    self.slow_requests.pop(0)
            
            # Update endpoint statistics
            self.endpoint_stats[endpoint].append(response_time)
            if len(self.endpoint_stats[endpoint]) > 100:
                self.endpoint_stats[endpoint].pop(0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        with self._lock:
            if not self.metrics:
                return {"status": "no_data"}
            
            # Calculate overall statistics
            response_times = [m.response_time for m in self.metrics]
            database_times = [m.database_time for m in self.metrics if m.database_time]
            cache_hits = [m.cache_hit for m in self.metrics if m.cache_hit is not None]
            
            summary = {
                "total_requests": len(self.metrics),
                "response_time_stats": {
                    "avg": sum(response_times) / len(response_times),
                    "min": min(response_times),
                    "max": max(response_times),
                    "p95": self._calculate_percentile(response_times, 95),
                    "p99": self._calculate_percentile(response_times, 99)
                },
                "database_performance": {
                    "avg_time": sum(database_times) / len(database_times) if database_times else 0,
                    "total_queries": len(database_times)
                },
                "cache_performance": {
                    "hit_rate": sum(cache_hits) / len(cache_hits) * 100 if cache_hits else 0,
                    "total_requests": len(cache_hits)
                },
                "slow_requests_count": len(self.slow_requests),
                "status_codes": self._get_status_code_distribution(),
                "timestamp": datetime.now().isoformat()
            }
            
            return summary
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from data list."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_status_code_distribution(self) -> Dict[str, int]:
        """Get distribution of HTTP status codes."""
        distribution = defaultdict(int)
        for metric in self.metrics:
            distribution[metric.status_code] += 1
        return dict(distribution)
    
    def get_endpoint_performance(self, endpoint: str) -> Dict[str, Any]:
        """Get performance statistics for a specific endpoint."""
        with self._lock:
            times = self.endpoint_stats.get(endpoint, [])
            if not times:
                return {"endpoint": endpoint, "status": "no_data"}
            
            return {
                "endpoint": endpoint,
                "request_count": len(times),
                "avg_response_time": sum(times) / len(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
                "p95_response_time": self._calculate_percentile(times, 95)
            }
    
    def get_slow_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow requests."""
        with self._lock:
            return self.slow_requests[-limit:] if self.slow_requests else []

class HealthChecker:
    """
    Comprehensive health check system for FineHero.
    Checks database, Redis, system resources, and overall application health.
    """
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.health_history = deque(maxlen=100)  # Keep 100 health checks
    
    def check_all(self) -> SystemHealth:
        """Perform comprehensive health check."""
        start_time = time.time()
        errors = []
        
        # System resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
        except Exception as e:
            cpu_percent = memory_percent = disk_percent = 0
            errors.append(f"System metrics error: {e}")
        
        # Database health
        try:
            db_health = db_health_check()
            database_status = db_health["status"]
            if database_status != "healthy":
                errors.append(f"Database status: {database_status}")
        except Exception as e:
            database_status = "error"
            errors.append(f"Database check failed: {e}")
        
        # Redis health
        try:
            redis_status = "healthy" if cache.is_connected() else "disconnected"
            if redis_status != "healthy":
                errors.append("Redis connection failed")
        except Exception as e:
            redis_status = "error"
            errors.append(f"Redis check failed: {e}")
        
        # Database connection count (if available)
        active_connections = 0
        try:
            if hasattr(db_config, 'engine') and db_config.engine:
                # This is a simplified connection count check
                active_connections = 1  # Placeholder
        except Exception:
            pass
        
        # Determine overall health status
        overall_status = self._determine_health_status(
            cpu_percent, memory.percent, disk.percent, 
            database_status, redis_status, errors
        )
        
        health = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            database_status=database_status,
            redis_status=redis_status,
            active_connections=active_connections,
            errors=errors
        )
        
        # Store in history
        self.health_history.append(health)
        
        # Log health status
        if overall_status != "healthy":
            logger.warning(f"System health degraded: {overall_status}. Errors: {errors}")
        
        return health
    
    def _determine_health_status(self, cpu_percent: float, memory_percent: float, 
                                disk_percent: float, db_status: str, redis_status: str,
                                errors: List[str]) -> str:
        """Determine overall health status based on metrics."""
        # Critical issues
        if db_status == "unhealthy" or redis_status == "error":
            return "unhealthy"
        
        # Resource issues
        if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
            return "unhealthy"
        
        # Warning level issues
        if cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
            return "degraded"
        
        # Minor issues
        if errors:
            return "degraded"
        
        return "healthy"
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        recent = list(self.health_history)[-limit:]
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "status": h.status,
                "cpu_percent": h.cpu_percent,
                "memory_percent": h.memory_percent,
                "disk_percent": h.disk_percent,
                "database_status": h.database_status,
                "redis_status": h.redis_status,
                "errors": h.errors
            }
            for h in recent
        ]

# Decorator for performance monitoring
def monitor_performance(performance_monitor: PerformanceMonitor):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            cache_hit = None
            database_time = None
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
                
            finally:
                # Record performance metrics
                response_time = time.time() - start_time
                
                # Extract endpoint info if available
                endpoint = getattr(func, '__name__', 'unknown')
                method = 'GET'  # Default, should be extracted from context
                
                performance_monitor.record_request(
                    endpoint=endpoint,
                    method=method,
                    response_time=response_time,
                    status_code=200,  # Should be extracted from actual response
                    database_time=database_time,
                    cache_hit=cache_hit
                )
        
        return wrapper
    return decorator

# Global instances
performance_monitor = PerformanceMonitor()
health_checker = HealthChecker(performance_monitor)

# Quick health check function for FastAPI
def quick_health_check() -> Dict[str, Any]:
    """Quick health check for monitoring endpoints."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_config.test_connection() else "disconnected",
        "cache": "connected" if cache.is_connected() else "disconnected",
        "uptime": time.time()  # Could track actual uptime
    }

# Export for use in other modules
__all__ = [
    "PerformanceMonitor",
    "HealthChecker", 
    "performance_monitor",
    "health_checker",
    "monitor_performance",
    "quick_health_check"
]