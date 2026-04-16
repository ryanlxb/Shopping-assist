"""Tests for platform adapter protocol and registry."""

from src.scraper.platform import PlatformScraper, get_scraper, PLATFORM_REGISTRY
from src.scraper.jd import JDScraper


class TestPlatformProtocol:
    def test_jd_scraper_is_platform_scraper(self):
        scraper = JDScraper()
        assert isinstance(scraper, PlatformScraper)

    def test_jd_scraper_platform_name(self):
        scraper = JDScraper()
        assert scraper.platform_name == "jd"


class TestPlatformRegistry:
    def test_registry_contains_jd(self):
        assert "jd" in PLATFORM_REGISTRY

    def test_get_scraper_returns_jd(self):
        scraper = get_scraper("jd")
        assert isinstance(scraper, JDScraper)
        assert scraper.platform_name == "jd"

    def test_get_scraper_unknown_raises(self):
        import pytest
        with pytest.raises(KeyError):
            get_scraper("unknown_platform")
