#!/usr/bin/env python3
"""
Production Deployment Script for FineHero Phase 3.
Handles database setup, dependency installation, and production configuration.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Production deployment automation for FineHero."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.root_dir = self.backend_dir.parent
        
    def install_dependencies(self, production: bool = True):
        """Install Python dependencies."""
        logger.info("Installing Python dependencies...")
        
        requirements_file = "requirements-production.txt" if production else "requirements.txt"
        requirements_path = self.backend_dir / requirements_file
        
        if not requirements_path.exists():
            logger.error(f"Requirements file not found: {requirements_path}")
            return False
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]
            subprocess.run(cmd, check=True, cwd=self.backend_dir)
            logger.info("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def setup_environment(self):
        """Set up production environment."""
        logger.info("Setting up environment...")
        
        env_example = self.backend_dir / ".env.example"
        env_file = self.backend_dir / ".env"
        
        if env_file.exists():
            logger.info(".env file already exists, skipping creation")
            return True
        
        if not env_example.exists():
            logger.error(".env.example file not found")
            return False
        
        try:
            # Copy example to actual .env
            import shutil
            shutil.copy(env_example, env_file)
            logger.info("Created .env file from .env.example")
            logger.warning("Please update .env file with your production values!")
            return True
        except Exception as e:
            logger.error(f"Failed to setup environment: {e}")
            return False
    
    def setup_database(self):
        """Initialize database tables."""
        logger.info("Setting up database...")
        
        try:
            # Create tables
            cmd = [
                sys.executable, "-c",
                "from app.models import Base; from database import engine; Base.metadata.create_all(bind=engine); print('Database tables created successfully')"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Database setup completed successfully")
                return True
            else:
                logger.error(f"Database setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database setup error: {e}")
            return False
    
    def test_connections(self):
        """Test database and Redis connections."""
        logger.info("Testing connections...")
        
        try:
            # Test database
            cmd = [
                sys.executable, "-c",
                "from database_enhanced import db_config; print('DB Test:', db_config.test_connection())"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Database connection test passed")
            else:
                logger.warning(f"Database connection test failed: {result.stderr}")
            
            # Test Redis (optional)
            try:
                cmd = [
                    sys.executable, "-c",
                    "from services.redis_cache import cache; print('Redis Test:', cache.is_connected())"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
                
                if result.returncode == 0:
                    logger.info("Redis connection test passed")
                else:
                    logger.warning(f"Redis connection test failed: {result.stderr}")
            except:
                logger.info("Redis not configured or test skipped")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False
    
    def run_health_check(self):
        """Run system health check."""
        logger.info("Running health check...")
        
        try:
            cmd = [
                sys.executable, "-c",
                "from services.performance_monitoring import quick_health_check; print(quick_health_check())"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Health check passed")
                logger.info(f"Health status: {result.stdout.strip()}")
                return True
            else:
                logger.warning(f"Health check failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def deploy(self, production: bool = True, skip_deps: bool = False, 
               skip_db: bool = False, skip_tests: bool = False):
        """Run complete deployment process."""
        logger.info(f"Starting FineHero {'production' if production else 'development'} deployment...")
        
        # Step 1: Install dependencies
        if not skip_deps:
            if not self.install_dependencies(production):
                logger.error("Deployment failed at dependency installation")
                return False
        
        # Step 2: Setup environment
        if not self.setup_environment():
            logger.error("Deployment failed at environment setup")
            return False
        
        # Step 3: Setup database
        if not skip_db:
            if not self.setup_database():
                logger.error("Deployment failed at database setup")
                return False
        
        # Step 4: Test connections
        if not skip_tests:
            if not self.test_connections():
                logger.warning("Connection tests failed - check your configuration")
        
        # Step 5: Health check
        if not skip_tests:
            if not self.run_health_check():
                logger.warning("Health check failed - deployment may have issues")
        
        logger.info("Deployment completed!")
        logger.info("Next steps:")
        logger.info("1. Update .env file with your production values")
        logger.info("2. Ensure PostgreSQL and Redis are running")
        logger.info("3. Start the application: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        
        return True

def main():
    """Main deployment script entry point."""
    parser = argparse.ArgumentParser(description="Deploy FineHero to production")
    parser.add_argument("--dev", action="store_true", help="Use development configuration")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-db", action="store_true", help="Skip database setup")
    parser.add_argument("--skip-tests", action="store_true", help="Skip connection tests")
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer()
    success = deployer.deploy(
        production=not args.dev,
        skip_deps=args.skip_deps,
        skip_db=args.skip_db,
        skip_tests=args.skip_tests
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()