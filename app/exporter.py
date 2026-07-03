from __future__ import annotations

import json
from pathlib import Path

from .config import PROJECT_ROOT
from .schemas import ResearchRun


OUTPUT_DIR = PROJECT_ROOT / "output"


def write_exports(run: ResearchRun) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "result.json").write_text(
        json.dumps(run.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "reply.md").write_text(_build_markdown(run), encoding="utf-8")


def _build_markdown(run: ResearchRun) -> str:
    sources = "\n".join(
        f"- [{source.title}]({source.url}) - {source.relevance or source.snippet}"
        if source.url
        else f"- {source.title} - {source.relevance or source.snippet}"
        for source in run.writer.cited_sources
    )
    if not sources:
        sources = "- Zdroje nebyly dostupne ve strukturovanem vystupu."

    source_quality = _build_source_quality_markdown(run)

    agent_log = "\n".join(
        (
            f"### {index}. {step.agent_name}\n\n"
            f"- Role: {step.role}\n"
            f"- Status: {step.status}\n"
            f"- Vstup: {step.input_summary}\n"
            f"- Vystup: {step.output_summary}\n"
            f"- Handoff: {step.handoff_summary}\n"
            f"- Tool calls: {len(step.tool_calls)}\n"
        )
        for index, step in enumerate(run.steps, start=1)
    )

    return (
        f"# {run.writer.title}\n\n"
        f"## Otazka\n\n{run.question}\n\n"
        f"## Finalni odpoved\n\n{run.final_answer}\n\n"
        f"## Zdroje\n\n{sources}\n\n"
        f"## Hodnoceni zdroju podle Source Quality Skill\n\n{source_quality}\n\n"
        f"## Agentni audit\n\n{agent_log}\n"
    )


def _build_source_quality_markdown(run: ResearchRun) -> str:
    if not run.analysis.source_quality:
        return "- Hodnoceni zdroju neni dostupne."

    rows = [
        "| Zdroj | Skore | Duvod |",
        "| --- | ---: | --- |",
    ]
    for source in run.analysis.source_quality:
        title = _markdown_source_title(source.title, source.url)
        rows.append(
            "| "
            f"{title} | "
            f"{source.score} | "
            f"{_escape_markdown_cell(source.reason)} |"
        )
    return "\n".join(rows)


def _markdown_source_title(title: str, url: str) -> str:
    safe_title = _escape_markdown_cell(title or url or "Zdroj bez nazvu")
    if not url:
        return safe_title
    return f"[{safe_title}]({url})"


def _escape_markdown_cell(value: str) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|").strip()
