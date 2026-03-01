from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    desc = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime)

class UserService(db.Model):
    __tablename__ = "users_services"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    service_id = db.Column(db.Integer)
    access = db.Column(db.Integer)