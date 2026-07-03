from __future__ import annotations

import json

from .config import get_model_name, get_search_model_name
from .exporter import write_exports
from .openai_client import run_json_chat, run_research_chat_with_tool
from .prompt_loader import load_prompt, load_source_quality_skill
from .schemas import (
    AgentStep,
    AnalysisResult,
    ResearchResult,
    ResearchRun,
    SourceItem,
    WriterResult,
)
from .tools import web_search


def process_research_question(question: str) -> ResearchRun:
    normalized_question = question.strip()
    if len(normalized_question) < 3:
        raise ValueError("Question is too short.")

    model = get_model_name()
    search_model = get_search_model_name()

    research_prompt = load_prompt("research")
    research_payload = (
        "Otazka uzivatele:\n"
        f"{normalized_question}\n\n"
        "Vytvor vhodny dotaz, zavolej web_search(query) a vrat JSON pro ResearchResult."
    )
    research_json, research_messages, research_tools = run_research_chat_with_tool(
        system_prompt=research_prompt,
        user_content=research_payload,
        web_search=web_search,
        model=model,
    )
    research = ResearchResult.model_validate(research_json)
    research_step = AgentStep(
        agent_name="Research Agent",
        role="Vyhleda webove zdroje a pripravi fakticky podklad.",
        status="done",
        input_summary=f"Uzivatelska otazka: {normalized_question}",
        output_summary=f"Pouzity dotaz: {research.search_query}; zdroju: {len(research.sources)}",
        handoff_summary="Predava seznam zdroju, shrnuti a mezery Analysis Agentovi.",
        system_prompt_excerpt=_excerpt(research_prompt),
        messages=research_messages,
        tool_calls=research_tools,
    )

    skill_text = load_source_quality_skill()
    analysis_prompt = load_prompt("analysis")
    analysis_payload = {
        "task": "Analyze research result with Source Quality Skill.",
        "question": normalized_question,
        "source_quality_skill": skill_text,
        "research_result": research.model_dump(mode="json"),
    }
    analysis_json, analysis_messages = run_json_chat(
        system_prompt=analysis_prompt,
        user_content=json.dumps(analysis_payload, ensure_ascii=False, indent=2),
        model=model,
    )
    analysis = AnalysisResult.model_validate(analysis_json)
    analysis_step = AgentStep(
        agent_name="Analysis Agent",
        role="Hodnoti kvalitu zdroju, hleda souvislosti a nejistoty.",
        status="done",
        input_summary=f"Prevzal {len(research.sources)} zdroju od Research Agenta a Source Quality Skill.",
        output_summary=f"Klicove zavery: {len(analysis.key_findings)}; rizika: {len(analysis.risks_or_uncertainties)}",
        handoff_summary="Predava syntézu, kvalitu zdroju a rizika Writer Agentovi.",
        system_prompt_excerpt=_excerpt(analysis_prompt),
        messages=analysis_messages,
        tool_calls=[],
    )

    writer_prompt = load_prompt("writer")
    writer_payload = {
        "task": "Write final structured answer for the user.",
        "question": normalized_question,
        "research_result": research.model_dump(mode="json"),
        "analysis_result": analysis.model_dump(mode="json"),
    }
    writer_json, writer_messages = run_json_chat(
        system_prompt=writer_prompt,
        user_content=json.dumps(writer_payload, ensure_ascii=False, indent=2),
        model=model,
    )
    writer = WriterResult.model_validate(writer_json)
    writer.cited_sources = _limit_sources_to_research(writer.cited_sources, research.sources)
    writer_step = AgentStep(
        agent_name="Writer Agent",
        role="Sestavi finalni strukturovanou odpoved pro uzivatele.",
        status="done",
        input_summary="Prevzal research podklad a syntézu Analysis Agenta.",
        output_summary=f"Finalni vystup: {writer.title}",
        handoff_summary="Vraci finalni odpoved do UI a exportu.",
        system_prompt_excerpt=_excerpt(writer_prompt),
        messages=writer_messages,
        tool_calls=[],
    )

    run = ResearchRun(
        question=normalized_question,
        final_answer=writer.final_answer,
        steps=[research_step, analysis_step, writer_step],
        research=research,
        analysis=analysis,
        writer=writer,
        model=model,
        search_model=search_model,
    )
    write_exports(run)
    return run


def _limit_sources_to_research(
    cited_sources: list[SourceItem],
    research_sources: list[SourceItem],
) -> list[SourceItem]:
    if not cited_sources:
        return research_sources[:5]
    known_urls = {source.url for source in research_sources if source.url}
    safe_sources = [
        source
        for source in cited_sources
        if not source.url or source.url in known_urls
    ]
    return safe_sources or research_sources[:5]


def _excerpt(text: str, limit: int = 420) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3] + "..."

