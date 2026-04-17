"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Shopping Assist"
    data_dir: str = "data"
    db_url: str = "sqlite:///data/shopping.db"
    max_daily_searches: int = 1
    max_products_per_search: int = 30
    ollama_model: str = "qwen2.5-vl:7b"
    ollama_base_url: str = "http://localhost:11434"
    scraper_headless: bool = True
    cdp_enabled: bool = True
    cdp_port: int = 9222

    model_config = {"env_prefix": "SA_"}


settings = Settings()
