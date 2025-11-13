"""
Database Indexing Migration for FineHero
Creates all missing indexes recommended in the examination report
"""

import logging
import time
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.postgresql_config import PostgreSQLConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseIndexingMigration:
    """
    Handles database indexing migration for FineHero
    """
    
    def __init__(self):
        self.postgresql_config = PostgreSQLConfig()
        self.engine = self.postgresql_config.create_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def run_migration(self):
        """
        Execute all database index migrations
        """
        logger.info("Starting database indexing migration...")
        
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Transaction to ensure all or nothing
                trans = conn.begin()
                
                # Step 1: Create compound indexes for common query patterns
                self._create_compound_indexes(conn)
                
                # Step 2: Create full-text search indexes
                self._create_fulltext_indexes(conn)
                
                # Step 3: Create partial indexes for filtered queries
                self._create_partial_indexes(conn)
                
                # Step 4: Create covering indexes (with INCLUDE clause)
                self._create_covering_indexes(conn)
                
                # Commit all changes
                trans.commit()
                
            elapsed_time = time.time() - start_time
            logger.info(f"Database indexing migration completed in {elapsed_time:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Database indexing migration failed: {e}")
            return False
    
    def _create_compound_indexes(self, conn):
        """
        Create compound indexes for frequently queried columns
        """
        logger.info("Creating compound indexes...")
        
        # 1. Legal documents by type and jurisdiction
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_legal_documents_type_jurisdiction 
            ON legal_documents(document_type, jurisdiction)
        """))
        
        # 2. Fines by user and date (for user fine history)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_user_date 
            ON fines(user_id, date DESC)
        """))
        
        # 3. Analytics events by user and timestamp
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_user_time 
            ON analytics_events(user_id, timestamp DESC)
        """))
        
        # 4. Defenses by user (for user defense history)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_defenses_user 
            ON defenses(user_id)
        """))
        
        # 5. Stripe subscriptions by customer and status
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer_status 
            ON stripe_subscriptions(customer_id, status)
        """))
        
        # 6. Payments by customer (for payment history)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_payments_customer 
            ON payments(customer_id)
        """))
        
        logger.info("Compound indexes created successfully")
    
    def _create_fulltext_indexes(self, conn):
        """
        Create full-text search indexes for text search operations
        """
        logger.info("Creating full-text search indexes...")
        
        # Legal documents text search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_legal_documents_search 
            ON legal_documents 
            USING GIN(to_tsvector('portuguese', extracted_text))
        """))
        
        # Defense content text search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_defenses_content_search 
            ON defenses 
            USING GIN(to_tsvector('portuguese', content))
        """))
        
        logger.info("Full-text search indexes created successfully")
    
    def _create_partial_indexes(self, conn):
        """
        Create partial indexes for filtered queries
        """
        logger.info("Creating partial indexes...")
        
        # Active subscription index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_active 
            ON stripe_subscriptions(customer_id, status) 
            WHERE status IN ('active', 'trialing')
        """))
        
        # Successful analytics events index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_success 
            ON analytics_events(user_id, timestamp DESC) 
            WHERE success = true
        """))
        
        # Uncanceled fines index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_active 
            ON fines(user_id, date DESC) 
            WHERE user_id IS NOT NULL
        """))
        
        logger.info("Partial indexes created successfully")
    
    def _create_covering_indexes(self, conn):
        """
        Create covering indexes with INCLUDE clause
        """
        logger.info("Creating covering indexes...")
        
        # Analytics events covering index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_user_time_covering 
            ON analytics_events(user_id, timestamp DESC) 
            INCLUDE (success, response_time, event_type)
        """))
        
        # Fines covering index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_user_date_covering 
            ON fines(user_id, date DESC) 
            INCLUDE (location, infraction_code, fine_amount)
        """))
        
        # Legal documents covering index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_legal_documents_type_covering 
            ON legal_documents(document_type, jurisdiction) 
            INCLUDE (title, source_url, quality_score)
        """))
        
        logger.info("Covering indexes created successfully")
    
    def create_foreign_key_indexes(self):
        """
        Create additional indexes on foreign key columns for better join performance
        """
        logger.info("Creating foreign key indexes...")
        
        try:
            with self.engine.connect() as conn:
                # Get all foreign keys that don't have indexes yet
                result = conn.execute(text("""
                    SELECT 
                        tc.table_name, 
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                      AND tc.table_schema = 'public'
                """)).fetchall()
                
                # Check for existing indexes
                for table_name, column_name, _, _ in result:
                    try:
                        # Check if index already exists
                        index_check = conn.execute(text("""
                            SELECT EXISTS (
                                SELECT 1 FROM pg_indexes 
                                WHERE schemaname = 'public' 
                                  AND tablename = :table_name 
                                  AND indexname = :index_name
                            )
                        """), {
                            "table_name": table_name,
                            "index_name": f"idx_{table_name}_{column_name}"
                        }).scalar()
                        
                        # Create index if it doesn't exist
                        if not index_check:
                            conn.execute(text(f"""
                                CREATE INDEX IF NOT EXISTS idx_{table_name}_{column_name}
                                ON {table_name}({column_name})
                            """))
                            logger.info(f"Created foreign key index: idx_{table_name}_{column_name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to create index for {table_name}.{column_name}: {e}")
                
                logger.info("Foreign key indexing completed")
                
        except Exception as e:
            logger.error(f"Foreign key indexing failed: {e}")
    
    def create_statistical_indexes(self):
        """
        Create indexes for statistical queries
        """
        logger.info("Creating statistical query indexes...")
        
        try:
            with self.engine.connect() as conn:
                # Analytics for date ranges
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp_range
                    ON analytics_events(timestamp)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_system_kpis_timestamp_range
                    ON system_kpis(timestamp)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_kpis_date_range
                    ON user_kpis(date)
                """))
                
                # Legal documents by publication date
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_legal_documents_publication_date
                    ON legal_documents(publication_date)
                """))
                
                # Stripe subscriptions by period dates
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_period
                    ON stripe_subscriptions(current_period_start, current_period_end)
                """))
                
                logger.info("Statistical indexes created successfully")
                
        except Exception as e:
            logger.error(f"Statistical indexing failed: {e}")

if __name__ == "__main__":
    migration = DatabaseIndexingMigration()
    migration.run_migration()
    migration.create_foreign_key_indexes()
    migration.create_statistical_indexes()