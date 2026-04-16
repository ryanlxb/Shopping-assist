"""FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload

from src.config import settings
from src.database import get_engine, get_session_factory, init_db
from src.models import Favorite, Ingredient, IngredientRule, Product, SearchTask
from src.ocr.service import OCRService
from src.scraper.platform import get_scraper
import src.scraper.jd  # noqa: F401 — register JD platform
import src.scraper.tb  # noqa: F401 — register TB platform
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

# Seed default ingredient rules on first run
from src.services.ingredient_knowledge import auto_seed_rules
with SessionFactory() as _session:
    _seeded = auto_seed_rules(_session)
    if _seeded:
        logger.info(f"Seeded {_seeded} default ingredient rules")


def _load_rules(session: Session) -> dict[str, set[str]]:
    """Load ingredient rules grouped by category."""
    rules = session.query(IngredientRule).all()
    grouped: dict[str, set[str]] = {"blacklist": set(), "whitelist": set(), "warning": set()}
    for rule in rules:
        grouped.setdefault(rule.category, set()).add(rule.name.lower())
    return grouped


def _classify_ingredient(name: str, rules: dict[str, set[str]]) -> dict:
    """Classify an ingredient and return its category and knowledge base info."""
    from src.services.ingredient_knowledge import lookup_additive

    name_lower = name.lower()
    category = "normal"
    for cat in ("blacklist", "whitelist", "warning"):
        if any(keyword in name_lower for keyword in rules.get(cat, set())):
            category = cat
            break

    kb_info = lookup_additive(name)
    return {
        "name": name,
        "category": category,
        "kb_type": kb_info["type"] if kb_info else None,
        "kb_desc": kb_info["desc"] if kb_info else None,
    }


def _load_products(
    session: Session,
    task_id: int,
    filter_query: str = "",
    exclude_blacklist: bool = False,
    sort_by: str = "",
) -> list[dict]:
    """Load products with ingredients for a task. Shared by results and filter routes."""
    products = (
        session.query(Product)
        .filter_by(search_task_id=task_id)
        .options(selectinload(Product.ingredients))
        .all()
    )

    rules = _load_rules(session)

    result = []
    for product in products:
        ingredient_names = [i.name for i in product.ingredients if i.name != "[未识别]"]

        if filter_query:
            if not any(filter_query.lower() in name.lower() for name in ingredient_names):
                continue

        # Classify each ingredient
        classified = []
        has_blacklist = False
        for name in ingredient_names:
            ci = _classify_ingredient(name, rules)
            classified.append(ci)
            if ci["category"] == "blacklist":
                has_blacklist = True

        if exclude_blacklist and has_blacklist:
            continue

        whitelist_count = sum(1 for c in classified if c["category"] == "whitelist")
        blacklist_count = sum(1 for c in classified if c["category"] == "blacklist")
        ingredient_score = whitelist_count - blacklist_count

        result.append({
            "product": product,
            "ingredients": product.ingredients,
            "ingredient_names": ingredient_names,
            "classified_ingredients": classified,
            "has_blacklist": has_blacklist,
            "ingredient_score": ingredient_score,
        })

    if sort_by == "price_asc":
        result.sort(key=lambda x: x["product"].price or float("inf"))
    elif sort_by == "price_desc":
        result.sort(key=lambda x: x["product"].price or 0, reverse=True)
    elif sort_by == "score_desc":
        result.sort(key=lambda x: x["ingredient_score"], reverse=True)

    return result


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Search page — main entry point."""
    with SessionFactory() as session:
        remaining = rate_limiter.remaining(session)
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
    platform: str = Form("jd"),
):
    """Create a new search task."""
    keyword = keyword.strip()
    if not keyword:
        return RedirectResponse("/?error=empty_keyword", status_code=303)

    if platform not in ("jd", "tb"):
        return RedirectResponse("/?error=invalid_platform", status_code=303)

    with SessionFactory() as session:
        if not rate_limiter.can_search(session):
            return RedirectResponse("/?error=rate_limit", status_code=303)

        scraper = get_scraper(platform, headless=settings.scraper_headless)
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

        return templates.TemplateResponse(
            request,
            "results.html",
            {
                "task": task,
                "products": _load_products(session, task_id),
            },
        )


@app.get("/results/{task_id}/filter", response_class=HTMLResponse)
async def filter_results(
    request: Request,
    task_id: int,
    q: str = Query("", max_length=100),
    no_blacklist: bool = Query(False),
    sort: str = Query(""),
):
    """Filter and sort products."""
    if sort not in ("", "price_asc", "price_desc", "score_desc"):
        sort = ""

    with SessionFactory() as session:
        task = session.query(SearchTask).filter_by(id=task_id).first()
        if not task:
            return RedirectResponse("/?error=not_found", status_code=303)

        q = q.strip()
        return templates.TemplateResponse(
            request,
            "results.html",
            {
                "task": task,
                "products": _load_products(session, task_id, filter_query=q, exclude_blacklist=no_blacklist, sort_by=sort),
                "filter_query": q,
                "no_blacklist": no_blacklist,
                "sort": sort,
            },
        )


@app.get("/ingredients/rules", response_class=HTMLResponse)
async def ingredient_rules_page(request: Request):
    """Ingredient rules management page."""
    with SessionFactory() as session:
        rules = session.query(IngredientRule).order_by(IngredientRule.category).all()
        grouped = {"blacklist": [], "whitelist": [], "warning": []}
        for rule in rules:
            grouped.setdefault(rule.category, []).append(rule)

        return templates.TemplateResponse(
            request,
            "rules.html",
            {"rules": grouped},
        )


@app.post("/ingredients/rules")
async def add_ingredient_rule(
    name: str = Form(..., max_length=200, min_length=1),
    category: str = Form(...),
    description: str = Form(""),
):
    """Add a new ingredient rule."""
    name = name.strip()
    if category not in ("blacklist", "whitelist", "warning"):
        return RedirectResponse("/ingredients/rules?error=invalid_category", status_code=303)

    with SessionFactory() as session:
        rule = IngredientRule(name=name, category=category, description=description.strip())
        session.add(rule)
        session.commit()

    return RedirectResponse("/ingredients/rules", status_code=303)


@app.post("/ingredients/rules/{rule_id}/delete")
async def delete_ingredient_rule(rule_id: int):
    """Delete an ingredient rule."""
    with SessionFactory() as session:
        rule = session.query(IngredientRule).filter_by(id=rule_id).first()
        if rule:
            session.delete(rule)
            session.commit()

    return RedirectResponse("/ingredients/rules", status_code=303)


# --- Favorites ---

@app.post("/favorites/{product_id}")
async def add_favorite(product_id: int):
    """Add a product to favorites."""
    with SessionFactory() as session:
        existing = session.query(Favorite).filter_by(product_id=product_id).first()
        if not existing:
            session.add(Favorite(product_id=product_id))
            session.commit()
    return RedirectResponse("/favorites", status_code=303)


@app.post("/favorites/{product_id}/delete")
async def remove_favorite(product_id: int):
    """Remove a product from favorites."""
    with SessionFactory() as session:
        fav = session.query(Favorite).filter_by(product_id=product_id).first()
        if fav:
            session.delete(fav)
            session.commit()
    return RedirectResponse("/favorites", status_code=303)


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request, sort: str = Query("")):
    """Display favorite products for comparison."""
    with SessionFactory() as session:
        favorites = (
            session.query(Favorite)
            .options(selectinload(Favorite.product).selectinload(Product.ingredients))
            .order_by(Favorite.created_at.desc())
            .all()
        )

        rules = _load_rules(session)
        items = []
        for fav in favorites:
            product = fav.product
            ingredient_names = [i.name for i in product.ingredients if i.name != "[未识别]"]
            classified = [_classify_ingredient(name, rules) for name in ingredient_names]
            whitelist_count = sum(1 for c in classified if c["category"] == "whitelist")
            blacklist_count = sum(1 for c in classified if c["category"] == "blacklist")

            items.append({
                "favorite": fav,
                "product": product,
                "classified_ingredients": classified,
                "ingredient_score": whitelist_count - blacklist_count,
            })

        if sort == "price_asc":
            items.sort(key=lambda x: x["product"].price or float("inf"))
        elif sort == "price_desc":
            items.sort(key=lambda x: x["product"].price or 0, reverse=True)
        elif sort == "score_desc":
            items.sort(key=lambda x: x["ingredient_score"], reverse=True)

        return templates.TemplateResponse(
            request,
            "favorites.html",
            {"items": items, "sort": sort},
        )
