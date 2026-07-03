from app.schemas import ResearchRequest, ResearchResult, SourceItem


def test_research_request_requires_non_empty_question():
    request = ResearchRequest(question="Jak AI meni e-commerce?")

    assert request.question.startswith("Jak")


def test_research_result_accepts_sources():
    result = ResearchResult(
        search_query="AI e-commerce trends",
        summary="Short summary",
        sources=[
            SourceItem(
                title="Example",
                url="https://example.com",
                snippet="Snippet",
                relevance="Relevant",
            )
        ],
    )

    assert result.sources[0].title == "Example"

