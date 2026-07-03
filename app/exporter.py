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
        f"## Agentni audit\n\n{agent_log}\n"
    )

