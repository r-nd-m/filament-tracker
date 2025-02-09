import pytest
from app import app, db
from app.models import FilamentRoll, PrintJob

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory DB for testing
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def init_database():
    """Populate the test database with initial data."""
    with app.app_context():  # Ensure we have an active application context
        filament1 = FilamentRoll(maker="Prusa", color="Black", total_weight=1000, remaining_weight=500, in_use=True)
        filament2 = FilamentRoll(maker="ESun", color="White", total_weight=750, remaining_weight=750, in_use=True)
        db.session.add_all([filament1, filament2])
        db.session.commit()
