import re
from typing import Dict, Optional
from urllib.parse import urlsplit

from flask import current_app, request

DEFAULT_TITLE = "REDTAIL | Remote Laboratory Simulations and Teaching Materials"
DEFAULT_DESCRIPTION = (
    "Explore REDTAIL simulations, digital twins, and teaching materials connected "
    "to real remote laboratory hardware."
)


def _plain_text(value: Optional[str], fallback: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", value or "").strip() or fallback
    if len(text) <= limit:
        return text

    shortened = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return f"{shortened}…"


def absolute_public_url(path: Optional[str] = None) -> str:
    public_base_url = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
    requested_path = path or request.path
    parsed = urlsplit(requested_path)
    normalized_path = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
    return f"{public_base_url}{normalized_path}"


def page_metadata(
    *,
    title: str = DEFAULT_TITLE,
    description: Optional[str] = None,
    canonical_path: Optional[str] = None,
) -> Dict[str, str]:
    return {
        "seo_title": re.sub(r"\s+", " ", title).strip() or DEFAULT_TITLE,
        "seo_description": _plain_text(description, DEFAULT_DESCRIPTION),
        "canonical_url": absolute_public_url(canonical_path),
    }
