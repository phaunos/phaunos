import os


SECRET_KEY = os.environ.get("SECRET_KEY", default=None)
if not SECRET_KEY:
    raise ValueError("No secret key set for Flask application")

POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_DB = os.environ['POSTGRES_DB']
POSTGRES_SERVER = os.environ['POSTGRES_SERVER']

SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

