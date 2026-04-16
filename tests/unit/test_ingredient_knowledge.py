"""Tests for ingredient knowledge base."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.database import Base
from src.models import IngredientRule
from src.services.ingredient_knowledge import lookup_additive, auto_seed_rules


class TestLookupAdditive:
    def test_exact_match(self):
        result = lookup_additive("山梨酸钾")
        assert result is not None
        assert result["category"] == "caution"
        assert result["type"] == "防腐剂"

    def test_partial_match_nfc(self):
        result = lookup_additive("橙汁(NFC)")
        assert result is not None
        assert result["category"] == "safe"

    def test_unknown_ingredient(self):
        assert lookup_additive("水") is None
        assert lookup_additive("白砂糖") is None

    def test_avoid_category(self):
        result = lookup_additive("苯甲酸钠")
        assert result["category"] == "avoid"


class TestAutoSeedRules:
    def test_seeds_rules_when_empty(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            count = auto_seed_rules(session)
            assert count > 0
            rules = session.query(IngredientRule).all()
            assert len(rules) == count

    def test_does_not_seed_when_rules_exist(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(IngredientRule(name="test", category="blacklist"))
            session.commit()
            count = auto_seed_rules(session)
            assert count == 0
