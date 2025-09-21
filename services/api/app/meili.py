from typing import Any

from meilisearch import Client
from .settings import settings

INDEX = "profiles"

def get_client() -> Client:
    return Client(settings.meili_host, settings.meili_master_key)


def _extract_task_uid(task: Any) -> Any:
    if task is None:
        return None
    if isinstance(task, dict):
        return task.get('taskUid') or task.get('uid')
    return getattr(task, 'task_uid', None) or getattr(task, 'uid', None)


def _wait_for_task(task: Any, client: Client | None = None) -> None:
    uid = _extract_task_uid(task)
    if uid is None:
        return
    (client or get_client()).wait_for_task(uid)


def ensure_indexes() -> None:
    client = get_client()
    try:
        client.get_index(INDEX)
    except Exception:
        create_task = client.create_index(INDEX, {"primaryKey": "id"})
        _wait_for_task(create_task, client)
    idx = client.index(INDEX)
    # Use default ranking rules and avoid invalid custom rules for Meilisearch v1.x
    # Custom ordering can be achieved via the `sort` parameter at query time.
    settings_task = idx.update_settings({
        "filterableAttributes": [
            "area", "bust_tag", "service_type", "body_tags", "price_min", "price_max", "status", "today",
            "height_cm", "age", "ranking_badges"
        ],
        "sortableAttributes": [
            "price_min", "price_max", "updated_at", "ctr7d", "today",
            "height_cm", "age", "ranking_weight"
        ],
        "searchableAttributes": ["name", "area", "body_tags"],
        # Keep default ranking rules; use `sort` at query time for ordering
        "rankingRules": [
            "words", "typo", "proximity", "attribute", "sort", "exactness"
        ],
    })
    _wait_for_task(settings_task, client)


def index_profile(doc: dict):
    client = get_client()
    task = client.index(INDEX).add_documents([doc])
    _wait_for_task(task, client)


def index_bulk(docs: list[dict]):
    if not docs:
        return
    client = get_client()
    task = client.index(INDEX).add_documents(docs)
    _wait_for_task(task, client)


def delete_profile(doc_id: str):
    client = get_client()
    task = client.index(INDEX).delete_document(doc_id)
    _wait_for_task(task, client)


def purge_all():
    """Delete all documents in the index (keeps settings)."""
    client = get_client()
    task = client.index(INDEX).delete_all_documents()
    _wait_for_task(task, client)


def build_filter(area: str | None, bust: str | None, service_type: str | None,
                 body_tags: list[str] | None, today: bool | None,
                 price_min: int | None, price_max: int | None, status: str | None) -> str | None:
    parts: list[str] = []
    if area:
        parts.append(f"area = '{area}'")
    if bust:
        parts.append(f"bust_tag = '{bust}'")
    if service_type:
        parts.append(f"service_type = '{service_type}'")
    if body_tags:
        for t in body_tags:
            parts.append(f"body_tags = '{t}'")
    if today is not None:
        parts.append(f"today = {'true' if today else 'false'}")
    if status:
        parts.append(f"status = '{status}'")
    rng: list[str] = []
    if price_min is not None:
        rng.append(f"price_min >= {price_min}")
    if price_max is not None:
        rng.append(f"price_max <= {price_max}")
    if rng:
        parts.extend(rng)
    if not parts:
        return None
    return " AND ".join(parts)


def search(q: str | None, filter_expr: str | None, sort: str | None, page: int, page_size: int,
           facets: list[str] | None = None) -> dict:
    idx = get_client().index(INDEX)
    options: dict = {"limit": page_size, "offset": (page - 1) * page_size}
    if filter_expr:
        options["filter"] = filter_expr
    if sort:
        options["sort"] = [sort]
    if facets:
        options["facets"] = facets
    # meilisearch-python >=0.30 expects the query as the first positional arg
    res = idx.search(q or "", options)
    return res
