class Config:
    SECRET_KEY = "change-this-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    VIDEO_FOLDER = "Videos"
    PORT = 5000