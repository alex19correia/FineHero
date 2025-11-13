"""
Test cases to verify N+1 query fixes
Tests the CRUD functions using eager loading to prevent N+1 queries
"""

import pytest
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import required modules
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import Session, relationship, sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Define test models
Base = declarative_base()

class TestUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)

class TestFine(Base):
    __tablename__ = "fines"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    location = Column(String)
    fine_amount = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship
    user = relationship("TestUser", back_populates="fines")
    defenses = relationship("TestDefense", back_populates="fine")

class TestDefense(Base):
    __tablename__ = "defenses"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    fine_id = Column(Integer, ForeignKey("fines.id"))
    
    # Relationship
    fine = relationship("TestFine", back_populates="defenses")

class TestUserWithRelationships(Base):
    __tablename__ = "users_relationships"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    
    # Relationship
    fines = relationship("TestFine", back_populates="user")

# Setup database connection
DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    os.remove("./test.db")

@pytest.fixture
def test_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_data(test_session):
    """Create test data for N+1 queries testing"""
    # Create users
    user1 = TestUser(email="user1@example.com")
    user2 = TestUser(email="user2@example.com")
    test_session.add_all([user1, user2])
    test_session.commit()
    
    # Create fines
    fine1 = TestFine(date="2025-01-01", location="Lisbon", fine_amount=100, user_id=user1.id)
    fine2 = TestFine(date="2025-01-02", location="Porto", fine_amount=200, user_id=user1.id)
    fine3 = TestFine(date="2025-01-03", location="Coimbra", fine_amount=150, user_id=user2.id)
    test_session.add_all([fine1, fine2, fine3])
    test_session.commit()
    
    # Create defenses
    defense1 = TestDefense(content="Defense content 1", fine_id=fine1.id)
    defense2 = TestDefense(content="Defense content 2", fine_id=fine1.id)
    defense3 = TestDefense(content="Defense content 3", fine_id=fine2.id)
    test_session.add_all([defense1, defense2, defense3])
    test_session.commit()
    
    return {
        "users": [user1, user2],
        "fines": [fine1, fine2, fine3],
        "defenses": [defense1, defense2, defense3]
    }

class TestNPlusOneFixes:
    """Test class for N+1 query fixes"""
    
    def test_get_fine_defenses_without_eager_loading(self, test_session, test_data):
        """Test to show the N+1 query problem without eager loading"""
        # This is how it would be done without eager loading (inefficient)
        fines = test_session.query(TestFine).filter(TestFine.user_id == test_data["users"][0].id).all()
        
        defenses = []
        for fine in fines:
            # This would cause N+1 queries in a real application
            fine_defenses = test_session.query(TestDefense).filter(TestDefense.fine_id == fine.id).all()
            defenses.extend(fine_defenses)
        
        assert len(defenses) == 3  # User1 has 2 fines with 3 defenses total
    
    def test_get_fine_defenses_with_eager_loading(self, test_session, test_data):
        """Test efficient query with eager loading using selectinload"""
        from sqlalchemy.orm import selectinload
        
        # This is the efficient way with eager loading
        fines = test_session.query(TestFine).options(
            selectinload(TestFine.defenses)
        ).filter(TestFine.user_id == test_data["users"][0].id).all()
        
        # Extract defenses from fines (no additional queries needed)
        defenses = []
        for fine in fines:
            defenses.extend(fine.defenses)
        
        assert len(defenses) == 3  # User1 has 2 fines with 3 defenses total
    
    def test_get_user_fines_with_defenses(self, test_session, test_data):
        """Test the get_user_fines_with_defenses function"""
        # Import the function from crud_fixes
        from backend.app.crud_fixes import get_user_fines_with_defenses
        
        # Call the function with eager loading
        fines = get_user_fines_with_defenses(
            test_session, 
            test_data["users"][0].id
        )
        
        # Extract defenses (no additional queries needed)
        defenses = []
        for fine in fines:
            defenses.extend(fine.defenses)
        
        assert len(fines) == 2  # User1 has 2 fines
        assert len(defenses) == 3  # User1 has 3 defenses across all fines
    
    def test_get_defense_with_fine(self, test_session, test_data):
        """Test the get_defense_with_fine function"""
        # Import the function from crud_fixes
        from backend.app.crud_fixes import get_defense_with_fine
        
        # Call the function with eager loading
        defense = get_defense_with_fine(
            test_session, 
            test_data["defenses"][0].id
        )
        
        assert defense is not None
        assert defense.id == test_data["defenses"][0].id
        assert defense.fine is not None
        assert defense.fine.id == test_data["defenses"][0].fine_id
    
    def test_get_fine_with_user(self, test_session, test_data):
        """Test the get_fine_with_user function"""
        # Import the function from crud_fixes
        from backend.app.crud_fixes import get_fine_with_user
        
        # Call the function with eager loading
        fine = get_fine_with_user(
            test_session, 
            test_data["fines"][0].id
        )
        
        assert fine is not None
        assert fine.id == test_data["fines"][0].id
        assert fine.user is not None
        assert fine.user.id == test_data["fines"][0].user_id
    
    def test_get_user_defenses_with_fines(self, test_session, test_data):
        """Test the get_user_defenses_with_fines function"""
        # Import the function from crud_fixes
        from backend.app.crud_fixes import get_user_defenses_with_fines
        
        # Call the function with eager loading
        defenses = get_user_defenses_with_fines(
            test_session, 
            test_data["users"][0].id
        )
        
        assert len(defenses) == 3  # User1 has 3 defenses
        # Check that all defenses are for the correct user
        for defense in defenses:
            assert defense.fine is not None
            assert defense.fine.user_id == test_data["users"][0].id
    
    def test_performance_comparison(self, test_session, test_data):
        """Test performance comparison between eager loading and N+1 queries"""
        from backend.app.crud_fixes import get_user_fines_with_defenses, detect_n_plus_one_queries
        import time
        
        # Test with eager loading (efficient)
        start_time = time.time()
        eager_results = get_user_fines_with_defenses(test_session, test_data["users"][0].id)
        eager_time = time.time() - start_time
        
        # Test with the detect function
        detect_results = detect_n_plus_one_queries(
            test_session, 
            get_user_fines_with_defenses, 
            test_data["users"][0].id
        )
        
        # Verify that the eager loading approach is fast
        assert len(eager_results) == 2  # User1 has 2 fines
        assert detect_results["results_count"] == 2
        # The eager loading should be fast (< 1 second for small dataset)
        assert detect_results["execution_time"] < 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])