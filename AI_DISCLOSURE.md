# AI and External-Service Disclosure

## AI-assisted build materials

As prepared in this work session on **28 October 2026**, ChatGPT assisted in generating an initial implementation of the BrandLens prototype, including portions of the FastAPI backend, frontend UI, automated test cases, and submission/setup documentation. The team must review, test, modify where appropriate, and understand the code before representing it as its submitted work. This disclosure must be updated to accurately record any further AI assistance, human changes, reused components and the actual dates of work.

## Runtime AI and external services

- **LLM/API calls in the prototype:** none.
- **External APIs:** none.
- **External data sources:** none at runtime.
- **Demo data:** fictional style rules, claim records and evidence labels bundled in the code. `DEMO-001`, `DEMO-002` and `DEMO-003` are not public evidence links.
- **Runtime fonts/assets:** system fonts and local HTML/CSS/JavaScript; no remote font or image resource is required.
- **Dependencies:** FastAPI, Uvicorn, pytest and httpx are listed in `requirements.txt` and are installed from package indexes during setup.

## Before submission

1. Confirm the event's official build window includes the dates when the meaningful implementation work happened.
2. Check the event's AI-use policy and submit this disclosure if required.
3. Update the disclosure after further code generation, model use, API integration or deployment work.
4. Ensure team members' contribution statements are factual and do not imply that AI-generated code was independently authored.
