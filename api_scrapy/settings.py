import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
    LOG_API_PATH: str = '/logs'

    @property
    def log_dir(self):
        return os.path.join(self.BASE_DIR, 'logs')

    @property
    def get_db_uri(self):
        return f"sqlite+aiosqlite:///{os.path.join(self.BASE_DIR, 'db.sqlite3')}"


config = Settings()
