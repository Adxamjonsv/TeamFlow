import os
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import pytz

class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ADMIN_IDS: Union[List[int], str] = []
    DATABASE_URL: str = "sqlite+aiosqlite:///tasks.db"
    TIMEZONE: str = "Asia/Tashkent"
    MORNING_REPORT_TIME: str = "09:00"
    EVENING_REPORT_TIME: str = "19:00"
    WEBAPP_URL: str = "http://localhost:8000"
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8000
    PORT: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v):
        if isinstance(v, str):
            # Railway / Heroku postgres URL moslashuvchanligi
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, list):
            return [int(x) for x in v if str(x).strip().isdigit()]
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                return []
            parts = clean.split(",")
            return [int(p.strip()) for p in parts if p.strip().isdigit()]
        return []

    @property
    def server_port(self) -> int:
        return self.PORT or self.WEBAPP_PORT

    @property
    def tz(self):
        return pytz.timezone(self.TIMEZONE)

settings = Settings()

