from __future__ import annotations

import json
import re
from typing import Any

from .config import get_model_name, get_openai_api_key
from .schemas import MessageRecord, ToolCallRecord


WEB_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the public web for current sources related to the user's research question.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A concise web search query.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


def build_messages(system_prompt: str, user_content: str) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def message_records(messages: list[dict[str, Any]]) -> list[MessageRecord]:
    records: list[MessageRecord] = []
    for message in messages:
        role = str(message.get("role", ""))
        content = message.get("content", "")
        if isinstance(content, str):
            records.append(MessageRecord(role=role, content=_compact(content)))
    return records


def run_json_chat(
    *,
    system_prompt: str,
    user_content: str,
    model: str | None = None,
) -> tuple[dict[str, Any], list[MessageRecord]]:
    messages = build_messages(system_prompt, user_content)
    response_text = _chat_completion_json(messages=messages, model=model or get_model_name())
    return parse_json_object(response_text), message_records(messages)


def run_research_chat_with_tool(
    *,
    system_prompt: str,
    user_content: str,
    web_search,
    model: str | None = None,
) -> tuple[dict[str, Any], list[MessageRecord], list[ToolCallRecord]]:
    from openai import OpenAI

    client = OpenAI(api_key=get_openai_api_key())
    selected_model = model or get_model_name()
    messages = build_messages(system_prompt, user_content)
    tool_records: list[ToolCallRecord] = []

    first = client.chat.completions.create(
        model=selected_model,
        messages=messages,
        tools=[WEB_SEARCH_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "web_search"}},
    )
    assistant_message = first.choices[0].message
    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:
        direct_result = web_search(_fallback_query_from_user_content(user_content))
        tool_records.append(
            ToolCallRecord(
                tool_name="web_search",
                arguments={"query": direct_result.get("query", "")},
                output_preview=_compact(json.dumps(direct_result, ensure_ascii=False)),
            )
        )
        messages.append(
            {
                "role": "user",
                "content": "Tool web_search byl spusten aplikaci jako fallback. Pouzij tento vysledek: "
                + json.dumps(direct_result, ensure_ascii=False),
            }
        )
    else:
        messages.append(_assistant_message_with_tool_calls(assistant_message))
        for tool_call in tool_calls:
            arguments = parse_json_object(tool_call.function.arguments or "{}")
            query = str(arguments.get("query", "")).strip() or _fallback_query_from_user_content(user_content)
            result = web_search(query)
            tool_output = json.dumps(result, ensure_ascii=False)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )
            tool_records.append(
                ToolCallRecord(
                    tool_name=tool_call.function.name,
                    arguments={"query": query},
                    output_preview=_compact(tool_output),
                )
            )

    second_text = _chat_completion_json(
        messages=messages,
        model=selected_model,
    )
    return parse_json_object(second_text), message_records(messages), tool_records


def _chat_completion_json(*, messages: list[dict[str, Any]], model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=get_openai_api_key())
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI response did not contain JSON content.")
    return content


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(text.strip())
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError(f"Expected JSON object, got: {cleaned[:200]}") from exc
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Expected JSON object.")
    return parsed


def _assistant_message_with_tool_calls(message) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            tool_call.model_dump(exclude_none=True)
            for tool_call in (message.tool_calls or [])
        ],
    }


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _compact(text: str, limit: int = 900) -> str:
    compacted = re.sub(r"\s+", " ", text).strip()
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3] + "..."


def _fallback_query_from_user_content(user_content: str) -> str:
    match = re.search(r"Otazka uzivatele:\s*(.+)", user_content, flags=re.DOTALL)
    if match:
        return match.group(1).strip()[:180]
    return user_content.strip()[:180]

