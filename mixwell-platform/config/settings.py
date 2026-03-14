import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

class Config:
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")
    SMTP_EMAIL = os.getenv("SMTP_EMAIL")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    SMTP_SERVER_G = os.getenv("SMTP_SERVER_G")
    SMTP_PORT_G = os.getenv("SMTP_PORT_G")
    SMTP_EMAIL_G = os.getenv("SMTP_EMAIL_G")
    SMTP_PASSWORD_G = os.getenv("SMTP_PASSWORD_G")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")

    JWT_SECRET = os.getenv("JWT_SECRET")
    AUTH_PORT = os.getenv("AUTH_PORT")
    SERVICE_URL = os.getenv("SERVICE_URL")
    GATEWAY_URL = os.getenv("GATEWAY_URL")
    ADMIN_NAME = os.getenv("ADMIN_NAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    PORTAL_PORT = os.getenv("PORTAL_PORT")
    VERIFY_URL = os.getenv("VERIFY_URL")
