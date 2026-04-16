"""E2E API tests for STORY-001: MVP core loop."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import Ingredient, Product, SearchTask  # noqa: F401 — import triggers table registration


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(db_engine):
    """Create a test client with in-memory database."""
    from src import app as app_module

    orig_factory = app_module.SessionFactory

    factory = sessionmaker(bind=db_engine)
    app_module.SessionFactory = factory

    yield TestClient(app_module.app)

    app_module.SessionFactory = orig_factory


class TestSearchPage:
    """TC-001 / AC1: Search page and form submission."""

    def test_index_page_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "商品配料表搜索" in response.text

    def test_index_shows_remaining_searches(self, client):
        response = client.get("/")
        assert "今日剩余搜索次数" in response.text

    def test_search_empty_keyword_redirects(self, client):
        response = client.post("/search", data={"keyword": "   "}, follow_redirects=False)
        assert response.status_code == 303
        assert "error=empty_keyword" in response.headers["location"]


class TestResultsPage:
    """TC-002 / AC2: Product list display."""

    def test_results_not_found_redirects(self, client):
        response = client.get("/results/9999", follow_redirects=False)
        assert response.status_code == 303
        assert "error=not_found" in response.headers["location"]

    def test_results_page_with_data(self, client, db_engine):
        factory = sessionmaker(bind=db_engine)
        with factory() as session:
            task = SearchTask(keyword="测试果汁", status="completed", result_count=1)
            session.add(task)
            session.flush()

            product = Product(
                search_task_id=task.id,
                name="NFC橙汁",
                price=12.9,
                shop_name="测试店铺",
                product_url="https://item.jd.com/1.html",
                platform="jd",
            )
            session.add(product)
            session.flush()

            session.add(Ingredient(
                product_id=product.id,
                name="橙汁(NFC)",
                raw_text="橙汁(NFC)",
                confidence="high",
            ))
            session.commit()

            response = client.get(f"/results/{task.id}")
            assert response.status_code == 200
            assert "NFC橙汁" in response.text
            assert "12.90" in response.text
            assert "测试店铺" in response.text
            assert "橙汁(NFC)" in response.text


class TestIngredientFilter:
    """TC-004 / AC4: Ingredient keyword filtering."""

    def _seed_data(self, db_engine):
        factory = sessionmaker(bind=db_engine)
        with factory() as session:
            task = SearchTask(keyword="果汁", status="completed", result_count=2)
            session.add(task)
            session.flush()

            p1 = Product(search_task_id=task.id, name="NFC橙汁", price=12.9,
                         shop_name="店铺A", product_url="https://jd.com/1", platform="jd")
            p2 = Product(search_task_id=task.id, name="浓缩橙汁", price=6.9,
                         shop_name="店铺B", product_url="https://jd.com/2", platform="jd")
            session.add_all([p1, p2])
            session.flush()

            session.add(Ingredient(product_id=p1.id, name="橙汁(NFC)", raw_text="橙汁(NFC)", confidence="high"))
            session.add(Ingredient(product_id=p2.id, name="浓缩橙汁", raw_text="浓缩橙汁", confidence="high"))
            session.add(Ingredient(product_id=p2.id, name="白砂糖", raw_text="白砂糖", confidence="high"))
            session.commit()
            return task.id

    def test_filter_shows_matching_products(self, client, db_engine):
        task_id = self._seed_data(db_engine)
        response = client.get(f"/results/{task_id}/filter?q=NFC")
        assert response.status_code == 200
        assert "NFC橙汁" in response.text
        assert "浓缩橙汁" not in response.text

    def test_filter_empty_shows_all(self, client, db_engine):
        task_id = self._seed_data(db_engine)
        response = client.get(f"/results/{task_id}/filter?q=")
        assert response.status_code == 200
        assert "NFC橙汁" in response.text
        assert "浓缩橙汁" in response.text

    def test_filter_no_match(self, client, db_engine):
        task_id = self._seed_data(db_engine)
        response = client.get(f"/results/{task_id}/filter?q=不存在的配料")
        assert response.status_code == 200
        assert "未找到含有" in response.text


class TestRateLimit:
    """TC-007 / AC7: Daily search rate limit."""

    def test_rate_limit_blocks_search(self, client, db_engine):
        factory = sessionmaker(bind=db_engine)
        with factory() as session:
            task = SearchTask(keyword="已用搜索", status="completed")
            session.add(task)
            session.commit()

        response = client.post("/search", data={"keyword": "新搜索"}, follow_redirects=False)
        assert response.status_code == 303
        assert "error=rate_limit" in response.headers["location"]
