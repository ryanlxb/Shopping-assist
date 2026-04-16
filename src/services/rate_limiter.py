"""Rate limiter for controlling search frequency."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models import SearchTask


class RateLimiter:
    def __init__(self, max_daily: int = 1):
        self.max_daily = max_daily

    def _today_count(self, session: Session) -> int:
        """Count search tasks created today (UTC)."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stmt = select(func.count()).select_from(SearchTask).where(
            func.date(SearchTask.created_at) == today_str
        )
        return session.execute(stmt).scalar() or 0

    def can_search(self, session: Session) -> bool:
        """Check if a new search is allowed today."""
        return self._today_count(session) < self.max_daily

    def remaining(self, session: Session) -> int:
        """Return how many searches remain today."""
        return max(0, self.max_daily - self._today_count(session))
