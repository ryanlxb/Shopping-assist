"""OCR service using Ollama with multimodal LLM (Qwen2.5-VL)."""

import base64
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

OCR_PROMPT = "请识别这张图片中的所有文字，特别是配料表信息。按原文输出，不要添加额外说明。"


class OCRService:
    def __init__(
        self,
        model: str = "qwen2.5-vl:7b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    async def recognize(self, image_path: str) -> dict:
        """Recognize text from an image using Ollama multimodal LLM.

        Returns dict with keys: text, confidence, error
        """
        try:
            image_data = Path(image_path).read_bytes()
            b64_image = base64.b64encode(image_data).decode("utf-8")

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": OCR_PROMPT,
                        "images": [b64_image],
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            text = data.get("response", "").strip()
            if not text:
                return {"text": None, "confidence": "low", "error": "Empty response"}

            return {"text": text, "confidence": "high", "error": None}

        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return {"text": None, "confidence": None, "error": str(e)}

    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
