"""FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.database import get_engine, get_session_factory, init_db
from src.models import Ingredient, Product, SearchTask
from src.ocr.service import OCRService
from src.scraper.jd import JDScraper
from src.services.rate_limiter import RateLimiter
from src.services.search import SearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

# Templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Static files (for images)
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# Database
engine = get_engine()
init_db(engine)
SessionFactory = get_session_factory(engine)

# Services
rate_limiter = RateLimiter(max_daily=settings.max_daily_searches)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Search page — main entry point."""
    with SessionFactory() as session:
        remaining = rate_limiter.remaining(session)
        # Get recent search tasks
        tasks = session.query(SearchTask).order_by(
            SearchTask.created_at.desc()
        ).limit(10).all()

        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "remaining_searches": remaining,
                "recent_tasks": tasks,
            },
        )


@app.post("/search")
async def create_search(
    request: Request,
    keyword: str = Form(..., max_length=100, min_length=1),
):
    """Create a new search task."""
    # Input validation
    keyword = keyword.strip()
    if not keyword:
        return RedirectResponse("/?error=empty_keyword", status_code=303)

    with SessionFactory() as session:
        # Rate limit check
        if not rate_limiter.can_search(session):
            return RedirectResponse("/?error=rate_limit", status_code=303)

        # Create and start search task
        scraper = JDScraper(headless=settings.scraper_headless)
        ocr = OCRService(model=settings.ollama_model, base_url=settings.ollama_base_url)
        service = SearchService(session=session, scraper=scraper, ocr=ocr)

        try:
            task = await service.execute_search(
                keyword=keyword,
                limit=settings.max_products_per_search,
            )
            return RedirectResponse(f"/results/{task.id}", status_code=303)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return RedirectResponse("/?error=search_failed", status_code=303)


@app.get("/results/{task_id}", response_class=HTMLResponse)
async def results(request: Request, task_id: int):
    """Display search results for a given task."""
    with SessionFactory() as session:
        task = session.query(SearchTask).filter_by(id=task_id).first()
        if not task:
            return RedirectResponse("/?error=not_found", status_code=303)

        products = session.query(Product).filter_by(
            search_task_id=task_id
        ).all()

        # Eager load ingredients
        products_with_ingredients = []
        for product in products:
            ingredients = session.query(Ingredient).filter_by(
                product_id=product.id
            ).all()
            products_with_ingredients.append({
                "product": product,
                "ingredients": ingredients,
                "ingredient_names": [i.name for i in ingredients if i.name != "[未识别]"],
            })

        return templates.TemplateResponse(
            request,
            "results.html",
            {
                "task": task,
                "products": products_with_ingredients,
            },
        )


@app.get("/results/{task_id}/filter", response_class=HTMLResponse)
async def filter_results(
    request: Request,
    task_id: int,
    q: str = Query("", max_length=100),
):
    """Filter products by ingredient keyword."""
    with SessionFactory() as session:
        task = session.query(SearchTask).filter_by(id=task_id).first()
        if not task:
            return RedirectResponse("/?error=not_found", status_code=303)

        products = session.query(Product).filter_by(
            search_task_id=task_id
        ).all()

        q = q.strip()
        products_with_ingredients = []
        for product in products:
            ingredients = session.query(Ingredient).filter_by(
                product_id=product.id
            ).all()
            ingredient_names = [i.name for i in ingredients if i.name != "[未识别]"]

            # Filter: if query provided, only include products with matching ingredients
            if q:
                if not any(q.lower() in name.lower() for name in ingredient_names):
                    continue

            products_with_ingredients.append({
                "product": product,
                "ingredients": ingredients,
                "ingredient_names": ingredient_names,
            })

        return templates.TemplateResponse(
            request,
            "results.html",
            {
                "task": task,
                "products": products_with_ingredients,
                "filter_query": q,
            },
        )
