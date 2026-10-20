"""Default-disabled local extraction preview; independent of news processing."""
from collections.abc import Callable
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.news import NewsArticle
from app.schemas.news_ner_preview import NerPreview
from app.services.news_ner.runtime import PreviewError
from app.services.news_ner_preview_service import ensure_enabled, preview_article


class NoStoreRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            try:
                response = await original(request)
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), 'Cache-Control': 'no-store'}
                raise
            except RequestValidationError as exc:
                response = JSONResponse({'detail': jsonable_encoder(exc.errors())}, status_code=422)
            except RateLimitExceeded as exc:
                raise HTTPException(429, detail={'code': 'preview_rate_limited'}, headers={'Cache-Control': 'no-store'}) from exc
            response.headers['Cache-Control'] = 'no-store'
            return response
        return handler


router = APIRouter(route_class=NoStoreRoute)


@router.post('/articles/{article_id}/ner-preview', response_model=NerPreview)
@limiter.limit('3/minute')
async def preview_saved_article_ner(
    request: Request,
    response: Response,
    article_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NerPreview:
    """Return transient extraction evidence; never creates or publishes a claim."""
    try:
        ensure_enabled(settings)
        article = db.get(NewsArticle, article_id)
        if article is None:
            raise PreviewError(404, 'article_not_found')
        return await preview_article(article)
    except SQLAlchemyError as exc:
        raise HTTPException(503, detail={'code': 'preview_storage_unavailable'}) from exc
    except PreviewError as exc:
        raise HTTPException(exc.status, detail={'code': exc.code}) from exc
