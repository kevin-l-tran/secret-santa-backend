import os

class BaseConfig:
    FRONTEND_URL   = os.environ.get("FRONTEND_URL")
    ROOM_ID_LENGTH = int(os.environ.get("ROOM_ID_LENGTH"))

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
