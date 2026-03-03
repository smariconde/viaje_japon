"""Configuración central — lee variables desde .env via Pydantic Settings."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio raíz del proyecto (dos niveles arriba de este archivo)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PRICE_HISTORY_FILE = DATA_DIR / "price_history.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Amadeus (fallback)
    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""

    # Configuración bot
    flight_price_threshold_usd: Annotated[float, Field(gt=0)] = 1200.0
    monitor_interval_minutes: Annotated[int, Field(gt=0)] = 60

    # Ruta de vuelo
    origin_iata: str = "EZE"
    destination_iata: str = "NRT,HND"
    target_months: str = "2027-02,2027-03"

    @property
    def destinations(self) -> list[str]:
        return [d.strip() for d in self.destination_iata.split(",")]

    @property
    def months(self) -> list[str]:
        return [m.strip() for m in self.target_months.split(",")]

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def amadeus_enabled(self) -> bool:
        return bool(self.amadeus_api_key and self.amadeus_api_secret)


# Instancia singleton
settings = Settings()
