import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Application
    APP_VERSION = os.getenv('APP_VERSION', 'blue')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'ecommerce')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

    # AWS
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    @property
    def DATABASE_URI(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

config = Config()
