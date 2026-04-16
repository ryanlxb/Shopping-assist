"""Tests for IngredientRule model and rule matching."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.database import Base
from src.models import IngredientRule


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


class TestIngredientRuleModel:
    def test_create_blacklist_rule(self, session):
        rule = IngredientRule(name="山梨酸钾", category="blacklist", description="防腐剂")
        session.add(rule)
        session.commit()

        result = session.execute(select(IngredientRule)).scalar_one()
        assert result.name == "山梨酸钾"
        assert result.category == "blacklist"

    def test_create_whitelist_rule(self, session):
        rule = IngredientRule(name="NFC", category="whitelist", description="非浓缩还原")
        session.add(rule)
        session.commit()

        result = session.execute(select(IngredientRule)).scalar_one()
        assert result.category == "whitelist"

    def test_create_warning_rule(self, session):
        rule = IngredientRule(name="阿斯巴甜", category="warning", description="人工甜味剂")
        session.add(rule)
        session.commit()

        result = session.execute(select(IngredientRule)).scalar_one()
        assert result.category == "warning"

    def test_query_by_category(self, session):
        rules = [
            IngredientRule(name="山梨酸钾", category="blacklist"),
            IngredientRule(name="苯甲酸钠", category="blacklist"),
            IngredientRule(name="NFC", category="whitelist"),
        ]
        session.add_all(rules)
        session.commit()

        blacklist = session.query(IngredientRule).filter_by(category="blacklist").all()
        assert len(blacklist) == 2

        whitelist = session.query(IngredientRule).filter_by(category="whitelist").all()
        assert len(whitelist) == 1
