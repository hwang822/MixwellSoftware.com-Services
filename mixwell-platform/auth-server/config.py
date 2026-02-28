import os

class Config:
    SECRET_KEY = "super-secret"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:delanyin00@localhost/authdb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "your@gmail.com"
    MAIL_PASSWORD = "app-password"

    JWT_SECRET = "jwt-secret"