from app.extensions import db
from datetime import datetime, timezone


# replicates the "items" table
class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.INT, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR(255), nullable=False)
    description = db.Column(db.TEXT)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    quantity = db.Column(db.INT, default=0)
    category_id = db.Column(db.INT)
    created_at = db.Column(db.DATETIME, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DATETIME, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Item {self.id}: {self.name}>'
