# Financial Document Analysis API

A multi-agent financial document analysis system built with **CrewAI** and **FastAPI**, orchestrating four specialized AI agents to process documents and deliver structured financial insights.

> 📋 **Setup & queue configuration** → [`QUEUE_SETUP.md`](./QUEUE_SETUP.md)
> 🚀 **Features & capabilities** → [`README_FEATURES.md`](./README_FEATURES.md)

---

## Bug Fixes

Eight bugs were identified and resolved across four source files during development.

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| 1 | `agents.py` | `from crewai.agents import Agent` — class is not exposed from that sub-module | Changed to `from crewai import Agent` |
| 2 | `agents.py` | `llm = llm` undefined; agent constructor had no LLM instance | Added proper LLM initialization with provider detection and stub fallback |
| 3 | `agents.py` | No API key fallback — raised `AuthenticationError` when key was missing | Added `_DummyLLM` subclass of `BaseLLM`; falls back gracefully if no key is set |
| 4 | `agents.py` | Used `tool=[…]` instead of `tools=[…]` in Agent constructors | Corrected to `tools=[]` (singular parameter is not recognized by CrewAI) |
| 5 | `tools.py` | `PyPDFLoader` used but never imported; `async` methods missing `self`; broken search tool import blocked startup | Added `PyPDFLoader` import; added `self` to all affected methods; replaced broken search tool with `None` |
| 6 | `main.py` | Route handler named `analyze_financial_document` shadowed the imported `Task` class | Renamed handler to `analyze_document` |
| 7 | `task.py` | All tasks wired to `financial_analyst` regardless of purpose; several tools referenced didn't exist | Assigned correct agents (`investment_advisor`, `risk_assessor`, `verifier`) to each task; removed invalid tool references |
| 8 | `main.py` | `Crew` was initialized with only one agent and one task — rest of the pipeline never ran | Registered all four agents and all four tasks in the `Crew` constructor |

### Notes

- **Bug 3** — If neither `OPENAI_API_KEY` nor `GOOGLE_API_KEY` is present, the app now starts using `_DummyLLM` which returns stub responses instead of crashing. Useful for local development without API costs.
- **Bug 8** — This was a silent failure: the server started and accepted requests, but only the first analysis step ever executed. All downstream agent outputs were empty.
