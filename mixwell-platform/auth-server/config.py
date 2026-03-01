import os

class Config:
    SECRET_KEY = "super-secret"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:delanyin00@localhost/authdb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "hwang822@gmail.com"
    MAIL_PASSWORD = "app-password"

    JWT_SECRET = "your_secret_key_here"
    EMAIL = "hwang822@gmail.com"
    EMAIL_SENDER = "donot_replay@mixwellsoftware.com"
    APP_PASSWORD = "srvx jcci adxk sfwl"
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    VERIFY_URL = "http://127.0.0.1:5003/user/verify/"
    