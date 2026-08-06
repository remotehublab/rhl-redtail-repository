import re
from typing import Dict, Iterable, Optional, Sequence, Tuple
from urllib.parse import urlsplit

from flask import current_app, request

DEFAULT_TITLE = "REDTAIL | Remote Laboratory Simulations and Teaching Materials"
DEFAULT_DESCRIPTION = (
    "Explore REDTAIL simulations, digital twins, and teaching materials connected "
    "to real remote laboratory hardware."
)

RHLAB_ORGANIZATION_ID = "https://rhlab.ece.uw.edu/#organization"

FACETED_ENDPOINTS = frozenset(
    {
        "public.devices",
        "public.laboratory_exercises",
        "public.simulations",
    }
)

NOINDEX_FOLLOW_ENDPOINTS = frozenset(
    {
        "login.login",
        "login.register",
        "public.md_viewer",
    }
)

NOINDEX_NOFOLLOW_ENDPOINTS = frozenset(
    {
        "public.file_submission",
        "public.replace_document",
        "public.serve_public",
        "public.serve_uploads",
        "public.simulation_device_doc_word",
        "public.simulation_doc_word",
        "public.word_converter",
    }
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


def public_asset_url(value: Optional[str] = None) -> str:
    fallback = "/static/img/redtail-social-card.png"
    parsed = urlsplit(value or fallback)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value or absolute_public_url(fallback)
    if parsed.scheme or parsed.netloc:
        return absolute_public_url(fallback)
    return absolute_public_url(parsed.path or fallback)


def page_metadata(
    *,
    title: str = DEFAULT_TITLE,
    description: Optional[str] = None,
    canonical_path: Optional[str] = None,
    image_url: Optional[str] = None,
    image_alt: Optional[str] = None,
    social_type: str = "website",
    structured_data: Optional[dict] = None,
) -> Dict[str, object]:
    return {
        "seo_title": re.sub(r"\s+", " ", title).strip() or DEFAULT_TITLE,
        "seo_description": _plain_text(description, DEFAULT_DESCRIPTION),
        "canonical_url": absolute_public_url(canonical_path),
        "seo_image_url": public_asset_url(image_url),
        "seo_image_alt": _plain_text(
            image_alt,
            "REDTAIL remote laboratory simulations and teaching materials",
            limit=120,
        ),
        "seo_social_type": social_type,
        "seo_structured_data": structured_data,
    }


def schema_graph(*nodes: Optional[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [node for node in nodes if node],
    }


def research_organization_schema() -> dict:
    return {
        "@type": "ResearchOrganization",
        "@id": RHLAB_ORGANIZATION_ID,
        "name": "Remote Hub Lab",
        "alternateName": "RHLab",
        "url": "https://rhlab.ece.uw.edu/",
        "logo": public_asset_url("/static/img/remote_hub_lab.png"),
        "email": "rhlab@uw.edu",
        "parentOrganization": {
            "@type": "CollegeOrUniversity",
            "name": "University of Washington",
            "url": "https://www.washington.edu/",
        },
        "sameAs": [
            "https://github.com/remotehublab",
            "https://rhlab.ece.uw.edu/",
        ],
    }


def website_schema() -> dict:
    site_url = absolute_public_url("/")
    return {
        "@type": "WebSite",
        "@id": f"{site_url}#website",
        "url": site_url,
        "name": "REDTAIL",
        "description": DEFAULT_DESCRIPTION,
        "publisher": {"@id": RHLAB_ORGANIZATION_ID},
    }


def breadcrumb_schema(items: Sequence[Tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": absolute_public_url(path),
            }
            for position, (name, path) in enumerate(items, start=1)
        ],
    }


def people_schema(authors: Iterable) -> list:
    people = []
    for author in authors:
        person = {"@type": "Person", "name": author.name}
        if author.link:
            person["url"] = author.link
        people.append(person)
    return people


def learning_resource_schema(
    *,
    name: str,
    description: str,
    path: str,
    image_url: Optional[str],
    resource_type: str,
    authors: Iterable,
    date_modified=None,
    educational_levels: Optional[Iterable[str]] = None,
    teaches: Optional[str] = None,
) -> dict:
    resource = {
        "@type": "LearningResource",
        "@id": f"{absolute_public_url(path)}#learning-resource",
        "url": absolute_public_url(path),
        "name": name,
        "description": _plain_text(description, DEFAULT_DESCRIPTION),
        "image": public_asset_url(image_url),
        "learningResourceType": resource_type,
        "educationalUse": "instruction",
        "interactivityType": "active",
        "author": people_schema(authors),
        "provider": {"@id": RHLAB_ORGANIZATION_ID},
        "isPartOf": {"@id": f"{absolute_public_url('/')}#website"},
    }
    if date_modified:
        resource["dateModified"] = date_modified.isoformat()
    levels = [level for level in educational_levels or [] if level]
    if levels:
        resource["educationalLevel"] = levels
    if teaches:
        resource["teaches"] = _plain_text(teaches, teaches, limit=500)
    return resource


def robots_directive(status_code: Optional[int] = None) -> Optional[str]:
    if status_code is not None and status_code >= 400:
        return "noindex, noarchive"

    endpoint = request.endpoint or ""
    if request.path == "/admin" or request.path.startswith("/admin/"):
        return "noindex, nofollow"
    if endpoint in NOINDEX_NOFOLLOW_ENDPOINTS:
        return "noindex, nofollow"
    if endpoint in NOINDEX_FOLLOW_ENDPOINTS:
        return "noindex, follow"
    if endpoint in FACETED_ENDPOINTS and request.args:
        return "noindex, follow"
    return None
