from __future__ import annotations

import json
from typing import Any

from .config import get_openai_api_key, get_search_model_name
from .openai_client import parse_json_object


def web_search(query: str) -> dict[str, Any]:
    """Search the web through OpenAI's built-in web_search tool."""
    from openai import OpenAI

    client = OpenAI(api_key=get_openai_api_key())
    prompt = (
        "Search the public web for the query below and return only valid JSON.\n"
        "Return 3-5 useful sources. Prefer primary, recent, and authoritative sources.\n\n"
        f"Query: {query}\n\n"
        "JSON shape:\n"
        "{\n"
        '  "query": "query used",\n'
        '  "summary": "short synthesis of search results",\n'
        '  "sources": [\n'
        '    {"title": "source title", "url": "https://...", "snippet": "short fact", "relevance": "why useful"}\n'
        "  ]\n"
        "}"
    )
    response = _create_web_search_response(client, prompt)
    raw_text = response.output_text
    try:
        result = parse_json_object(raw_text)
    except Exception:
        result = {
            "query": query,
            "summary": raw_text,
            "sources": [],
        }
    result.setdefault("query", query)
    result.setdefault("summary", "")
    result.setdefault("sources", [])
    return _normalize_search_result(result)


def _create_web_search_response(client, prompt: str):
    search_model = get_search_model_name()
    try:
        return client.responses.create(
            model=search_model,
            tools=[{"type": "web_search"}],
            input=prompt,
        )
    except Exception:
        return client.responses.create(
            model=search_model,
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )


def _normalize_search_result(result: dict[str, Any]) -> dict[str, Any]:
    sources = result.get("sources", [])
    if not isinstance(sources, list):
        sources = []

    normalized_sources: list[dict[str, str]] = []
    for source in sources[:5]:
        if not isinstance(source, dict):
            continue
        normalized_sources.append(
            {
                "title": str(source.get("title", "Untitled source")),
                "url": str(source.get("url", "")),
                "snippet": str(source.get("snippet", "")),
                "relevance": str(source.get("relevance", "")),
            }
        )

    return {
        "query": str(result.get("query", "")),
        "summary": str(result.get("summary", "")),
        "sources": normalized_sources,
        "raw": json.dumps(result, ensure_ascii=False)[:3000],
    }
