# Multi-agentní výzkumný asistent

Jednoduchá lokální webová aplikace pro case study na pozici AI implementátora. Uživatel zadá téma nebo otázku a aplikace ji zpracuje přes tři explicitní subagenty:

```text
Research Agent -> Analysis/Synthesis Agent -> Writer Agent
```

Aplikace běží lokálně přes FastAPI a webové UI na `http://127.0.0.1:8000`.

## Co aplikace splňuje

- Webové UI s jedním vstupem pro otázku.
- Přímé volání OpenAI API přes `openai` Python SDK, bez LangChain a bez `openai-agents`.
- Viditelná práce s `messages`, system prompty a tools v kódu i auditním výstupu.
- Research Agent má tool `web_search(query)`, který je modelu předán jako function-calling tool.
- Analysis Agent reálně používá vlastní skill `skills/source_quality/SKILL.md`.
- Handoff mezi agenty je explicitní v `app/orchestrator.py`.
- UI ukazuje stav, tool call, výstup a rozbalovací detail `messages / system prompt / tools` pro každý agentní krok.
- Výstup se ukládá do `output/result.json` a `output/reply.md`.

## Instalace

```bash
cd /Users/Martin/Documents/Codex/Python/case-study-addvery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Spuštění

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Potom otevřít:

```text
http://127.0.0.1:8000
```

## OpenAI API key

Aplikace používá OpenAI API přes balíček `openai`. Je potřeba vložit `OPENAI_API_KEY` z OpenAI Platform. Nepoužívejte Claude/Anthropic API key, protože ho tato aplikace neumí použít.

API klíč se nevkládá do Gitu. Po prvním spuštění ho lze vložit přímo ve webovém UI do pole `OpenAI API key (OPENAI_API_KEY)`. Backend ho uloží do lokálního `.env`, který je v `.gitignore`.

Do repozitáře patří jen `.env.example`:

```text
# Vlozte OpenAI API key. Nepouzivejte Claude/Anthropic API key.
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
OPENAI_SEARCH_MODEL=gpt-5.5
```

Jakmile je OpenAI `OPENAI_API_KEY` uložený, panel pro vložení klíče se v UI schová.

## Architektura

```text
static/index.html        webové UI
static/app.js            volání API a vykreslení agentních kroků
static/styles.css        jednoduchý responzivní vzhled
app/main.py              FastAPI endpointy
app/orchestrator.py      explicitní pipeline Research -> Analysis -> Writer
app/openai_client.py     přímá OpenAI API volání, messages a function calling
app/tools.py             implementace web_search(query)
app/prompts/*.md         system prompty agentů
skills/source_quality/   vlastní skill používaný Analysis Agentem
tests/                   testy bez volání OpenAI API
```

## Messages, system prompt a tools

Každý agent dostává vlastní system prompt ze souboru v `app/prompts/`.

V `app/openai_client.py` se ručně skládají `messages`, například:

```python
[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_content}
]
```

Research Agent navíc dostává function-calling tool:

```python
{
    "type": "function",
    "function": {
        "name": "web_search",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
}
```

Když model požádá o `web_search(query)`, backend funkci skutečně zavolá a výsledek vrátí modelu jako `tool` zprávu.

## Handoffy

Handoff je v kódu explicitní:

1. Research Agent vrací `ResearchResult`: dotaz, shrnutí, zdroje a mezery.
2. Analysis Agent dostane `ResearchResult` plus `SKILL.md` a vrací `AnalysisResult`.
3. Writer Agent dostane `ResearchResult` i `AnalysisResult` a vrací finální odpověď.

Nejde o jeden velký prompt. Každý agent má vlastní prompt, vlastní vstup a vlastní strukturovaný výstup.

## Testy

```bash
source .venv/bin/activate
pytest
```

Testy nevolají OpenAI API.
