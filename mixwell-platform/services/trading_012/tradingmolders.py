from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    side = db.Column(db.String(10))
    price = db.Column(db.Float)
    qty = db.Column(db.Float)
    pnl = db.Column(db.Float)
    reason = db.Column(db.String(100))
    transaction_time = db.Column(db.DateTime, default=datetime.utcnow)