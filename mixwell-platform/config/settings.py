import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    VERIFY_URL = os.getenv("VERIFY_URL")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    JWT_SECRET = os.getenv("JWT_SECRET")
    AUTH_PORT = os.getenv("AUTH_PORT")
    AUTH_URL = os.getenv("AUTH_URL")
