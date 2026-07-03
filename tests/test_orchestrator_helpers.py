from app.orchestrator import _limit_sources_to_research
from app.schemas import SourceItem


def test_writer_sources_are_limited_to_research_sources():
    research_sources = [
        SourceItem(title="Allowed", url="https://allowed.example", snippet="A"),
    ]
    cited_sources = [
        SourceItem(title="Allowed", url="https://allowed.example", snippet="A"),
        SourceItem(title="Invented", url="https://invented.example", snippet="B"),
    ]

    result = _limit_sources_to_research(cited_sources, research_sources)

    assert len(result) == 1
    assert result[0].url == "https://allowed.example"

