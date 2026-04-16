"""Tests for rate limiter service."""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.database import Base
from src.models import SearchTask
from src.services.rate_limiter import RateLimiter


class TestRateLimiter:
    def _make_session(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return Session(engine)

    def test_allows_first_search_of_day(self):
        session = self._make_session()
        limiter = RateLimiter(max_daily=1)
        assert limiter.can_search(session) is True

    def test_blocks_after_limit_reached(self):
        session = self._make_session()
        limiter = RateLimiter(max_daily=1)

        task = SearchTask(keyword="测试", status="completed")
        session.add(task)
        session.commit()

        assert limiter.can_search(session) is False

    def test_allows_multiple_within_limit(self):
        session = self._make_session()
        limiter = RateLimiter(max_daily=3)

        for i in range(2):
            session.add(SearchTask(keyword=f"测试{i}", status="completed"))
        session.commit()

        assert limiter.can_search(session) is True

    def test_remaining_count(self):
        session = self._make_session()
        limiter = RateLimiter(max_daily=5)

        session.add(SearchTask(keyword="测试", status="completed"))
        session.commit()

        assert limiter.remaining(session) == 4
