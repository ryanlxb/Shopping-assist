"""Platform scraper protocol — unified interface for all e-commerce scrapers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class PlatformScraper(Protocol):
    """Interface that all platform scrapers must implement."""

    platform_name: str

    async def search(self, keyword: str, limit: int = 30) -> list[dict]: ...

    async def get_detail(self, product_url: str) -> dict: ...

    async def download_images(self, image_urls: list[str], product_id: str) -> list[str]: ...

    async def close(self) -> None: ...


# Registry of available platform scrapers
PLATFORM_REGISTRY: dict[str, type] = {}


def register_platform(name: str):
    """Decorator to register a scraper class in the platform registry."""
    def wrapper(cls):
        PLATFORM_REGISTRY[name] = cls
        return cls
    return wrapper


def get_scraper(platform: str, **kwargs) -> PlatformScraper:
    """Get a scraper instance by platform name."""
    if platform not in PLATFORM_REGISTRY:
        raise KeyError(f"Unknown platform: {platform}. Available: {list(PLATFORM_REGISTRY.keys())}")
    return PLATFORM_REGISTRY[platform](**kwargs)
