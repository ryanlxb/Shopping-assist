"""Tests for SQLAlchemy data models and database operations."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.database import Base
from src.models import Ingredient, Product, SearchTask


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


class TestSearchTask:
    def test_create_search_task(self, session):
        task = SearchTask(keyword="NFC果汁", status="pending")
        session.add(task)
        session.commit()

        result = session.execute(select(SearchTask)).scalar_one()
        assert result.keyword == "NFC果汁"
        assert result.status == "pending"
        assert result.result_count == 0
        assert result.created_at is not None

    def test_search_task_status_update(self, session):
        task = SearchTask(keyword="酱油", status="pending")
        session.add(task)
        session.commit()

        task.status = "completed"
        task.result_count = 15
        session.commit()

        result = session.execute(select(SearchTask)).scalar_one()
        assert result.status == "completed"
        assert result.result_count == 15


class TestProduct:
    def test_create_product_with_task(self, session):
        task = SearchTask(keyword="果汁", status="completed")
        session.add(task)
        session.flush()

        product = Product(
            search_task_id=task.id,
            name="农夫山泉NFC橙汁",
            price=12.9,
            shop_name="农夫山泉自营旗舰店",
            product_url="https://item.jd.com/123456.html",
            platform="jd",
            thumbnail_path="data/images/thumb_123.jpg",
        )
        session.add(product)
        session.commit()

        result = session.execute(select(Product)).scalar_one()
        assert result.name == "农夫山泉NFC橙汁"
        assert result.price == 12.9
        assert result.platform == "jd"
        assert result.search_task_id == task.id

    def test_product_task_relationship(self, session):
        task = SearchTask(keyword="果汁", status="completed", result_count=1)
        session.add(task)
        session.flush()

        product = Product(
            search_task_id=task.id,
            name="测试商品",
            price=9.9,
            shop_name="测试店铺",
            product_url="https://item.jd.com/1.html",
            platform="jd",
        )
        session.add(product)
        session.commit()

        result = session.execute(select(Product)).scalar_one()
        assert result.search_task.keyword == "果汁"
        assert len(task.products) == 1


class TestIngredient:
    def test_create_ingredient(self, session):
        task = SearchTask(keyword="果汁", status="completed")
        session.add(task)
        session.flush()

        product = Product(
            search_task_id=task.id,
            name="NFC橙汁",
            price=12.9,
            shop_name="店铺",
            product_url="https://item.jd.com/1.html",
            platform="jd",
        )
        session.add(product)
        session.flush()

        ingredient = Ingredient(
            product_id=product.id,
            name="橙汁(NFC)",
            raw_text="配料：橙汁(NFC)",
            image_path="data/images/ingredients_1.jpg",
            confidence="high",
        )
        session.add(ingredient)
        session.commit()

        result = session.execute(select(Ingredient)).scalar_one()
        assert result.name == "橙汁(NFC)"
        assert result.confidence == "high"
        assert result.product.name == "NFC橙汁"

    def test_product_ingredients_relationship(self, session):
        task = SearchTask(keyword="果汁", status="completed")
        session.add(task)
        session.flush()

        product = Product(
            search_task_id=task.id,
            name="NFC橙汁",
            price=12.9,
            shop_name="店铺",
            product_url="https://item.jd.com/1.html",
            platform="jd",
        )
        session.add(product)
        session.flush()

        ingredients = [
            Ingredient(product_id=product.id, name="橙汁(NFC)", raw_text="橙汁(NFC)", confidence="high"),
            Ingredient(product_id=product.id, name="维生素C", raw_text="维生素C", confidence="high"),
        ]
        session.add_all(ingredients)
        session.commit()

        assert len(product.ingredients) == 2
        names = [i.name for i in product.ingredients]
        assert "橙汁(NFC)" in names
        assert "维生素C" in names
