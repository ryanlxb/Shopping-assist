"""Search orchestration service — coordinates scraper, OCR, and database."""

import logging

from sqlalchemy.orm import Session

from src.models import Ingredient, Product, SearchTask
from src.ocr.ingredient_parser import parse_ingredients
from src.ocr.service import OCRService
from src.scraper.jd import JDScraper
from src.scraper.platform import PlatformScraper

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(
        self,
        session: Session,
        scraper: PlatformScraper | None = None,
        ocr: OCRService | None = None,
    ):
        self.session = session
        self.scraper = scraper or JDScraper()
        self.ocr = ocr or OCRService()

    async def execute_search(self, keyword: str, limit: int = 30) -> SearchTask:
        """Execute a full search: scrape → parse → OCR → save."""
        # Create task record
        task = SearchTask(keyword=keyword, status="running")
        self.session.add(task)
        self.session.commit()

        try:
            # Step 1: Search for products
            raw_products = await self.scraper.search(keyword, limit=limit)
            logger.info(f"Found {len(raw_products)} products for '{keyword}'")

            # Step 2: Process each product
            for raw in raw_products:
                product = Product(
                    search_task_id=task.id,
                    name=raw["name"],
                    price=raw.get("price"),
                    shop_name=raw.get("shop_name"),
                    product_url=raw["product_url"],
                    platform=self.scraper.platform_name,
                    thumbnail_path=raw.get("thumbnail_url"),
                )
                self.session.add(product)
                self.session.flush()

                # Step 3: Get detail page
                detail = await self.scraper.get_detail(raw["product_url"])

                # Step 4: Handle text-based ingredients
                if detail.get("ingredient_text"):
                    ingredient_names = parse_ingredients(detail["ingredient_text"])
                    for name in ingredient_names:
                        self.session.add(Ingredient(
                            product_id=product.id,
                            name=name,
                            raw_text=detail["ingredient_text"],
                            confidence="high",
                        ))

                # Step 5: Handle image-based ingredients (OCR)
                elif detail.get("image_urls"):
                    image_paths = await self.scraper.download_images(
                        detail["image_urls"], str(product.id)
                    )
                    for img_path in image_paths:
                        ocr_result = await self.ocr.recognize(img_path)
                        if ocr_result["text"]:
                            ingredient_names = parse_ingredients(ocr_result["text"])
                            for name in ingredient_names:
                                self.session.add(Ingredient(
                                    product_id=product.id,
                                    name=name,
                                    raw_text=ocr_result["text"],
                                    image_path=img_path,
                                    confidence=ocr_result.get("confidence", "low"),
                                ))
                        else:
                            # OCR failed — record the image path for display
                            self.session.add(Ingredient(
                                product_id=product.id,
                                name="[未识别]",
                                image_path=img_path,
                                confidence="none",
                            ))

            # Finalize
            task.status = "completed"
            task.result_count = len(raw_products)
            self.session.commit()
            logger.info(f"Search task {task.id} completed: {task.result_count} products")

        except Exception as e:
            task.status = "failed"
            self.session.commit()
            logger.error(f"Search task {task.id} failed: {e}")
            raise

        finally:
            await self.scraper.close()

        return task
