"""Tests for OCR service and ingredient parser."""

from unittest.mock import AsyncMock, patch

import pytest

from src.ocr.service import OCRService
from src.ocr.ingredient_parser import parse_ingredients


class TestOCRService:
    @pytest.fixture
    def ocr_service(self):
        return OCRService(model="qwen2.5-vl:7b", base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_recognize_returns_text(self, ocr_service):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {"response": "配料：橙汁(NFC)，维生素C"}

        with patch("pathlib.Path.read_bytes", return_value=b"fake_image_data"), \
             patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await ocr_service.recognize("data/images/test.jpg")
            assert "橙汁" in result["text"]
            assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_recognize_handles_service_unavailable(self, ocr_service):
        with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
            result = await ocr_service.recognize("data/images/test.jpg")
            assert result["text"] is None
            assert result["confidence"] is None
            assert result["error"] is not None

    def test_check_health_url(self, ocr_service):
        assert ocr_service.base_url == "http://localhost:11434"


class TestIngredientParser:
    def test_parse_simple_ingredients(self):
        text = "配料：橙汁(NFC)，维生素C，柠檬酸"
        ingredients = parse_ingredients(text)
        assert len(ingredients) == 3
        assert "橙汁(NFC)" in ingredients

    def test_parse_ingredients_with_chinese_comma(self):
        text = "配料表：水、白砂糖、食用盐、酿造酱油"
        ingredients = parse_ingredients(text)
        assert "水" in ingredients
        assert "白砂糖" in ingredients

    def test_parse_empty_text(self):
        assert parse_ingredients("") == []
        assert parse_ingredients(None) == []

    def test_parse_ingredients_strips_prefix(self):
        text = "配料：橙汁"
        ingredients = parse_ingredients(text)
        assert ingredients == ["橙汁"]

    def test_parse_ingredients_with_mixed_separators(self):
        text = "原料：水,浓缩橙汁、白砂糖，食品添加剂(柠檬酸)"
        ingredients = parse_ingredients(text)
        assert len(ingredients) >= 3
