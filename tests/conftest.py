from typing import Any, Generator

import pytest

from datetime import datetime
from decimal import Decimal

from flask import Flask

from app import create_app
from app.extensions import db
from app.schemas import Item

@pytest.fixture
def app() -> Generator[Flask, Any, None]:
    """Create and configure a test app."""
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",    # In-memory SQLite for testing
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False                           # todo - What is this?
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app: Flask):
    """Return a test client for the app"""
    return app.test_client()

# todo - What is this?
@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def sample_items(app: Flask) -> list[Item]:
    """Create sample items for testing."""
    with app.app_context():
        items = [
            Item(
                name="Laptop",
                description="High-performance laptop",
                price=Decimal("999.99"),
                quantity=10,
                category_id=1,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0)
            ),
            Item(
                name="Mouse",
                description="Wireless mouse",
                price=Decimal("29.99"),
                quantity=25,
                category_id=2,
                created_at=datetime(2024, 1, 2, 12, 0, 0),
                updated_at=datetime(2024, 1, 2, 12, 0, 0)
            ),
            Item(
                name="Keyboard",
                description="Mechanical keyboard",
                price=Decimal("89.99"),
                quantity=15,
                category_id=2,
                created_at=datetime(2024, 1, 3, 12, 0, 0),
                updated_at=datetime(2024, 1, 3, 12, 0, 0)
            ),
            Item(
                name="Monitor",
                description="4K monitor",
                price=Decimal("299.99"),
                quantity=8,
                category_id=1,
                created_at=datetime(2024, 1, 4, 12, 0, 0),
                updated_at=datetime(2024, 1, 4, 12, 0, 0)
            ),
            Item(
                name="Headphones",
                description="Noise-canceling headphones",
                price=Decimal("199.99"),
                quantity=12,
                category_id=3,
                created_at=datetime(2024, 1, 5, 12, 0, 0),
                updated_at=datetime(2024, 1, 5, 12, 0, 0)
            )
        ]

        db.session.add_all(items)
        db.session.commit()

        return items
