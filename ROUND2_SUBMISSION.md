# BrandLens — Round 2 Submission: The Build

**Team:** NEXORA  
**Problem statement:** Inkloom AI — Intelligent Brand-Governance Platform  
**Build package date:** 28 October 2026  
**Submission status:** Local functional prototype + source package; public repository, public deployment and real user feedback are not yet supplied.

> **Eligibility and AI disclosure:** The problem statement requires meaningful product work to occur within the official build window and warns that work outside it may lead to disqualification. This prototype was generated with AI assistance on 28 October 2026. The team must verify the official window and disclosure requirements before submission, review and understand the code, and accurately describe each member's actual contribution. Do not backdate commits or claim that AI-generated material was independently authored.

## 1. Product overview

BrandLens is a source-grounded, human-controlled pre-publication review workflow. The MVP accepts draft text and checks it against a small fictional brand rule library and approved-claims ledger. Findings show the affected text, severity, rationale, cited rule or claim record, and a suggested next step. Users can accept a suggestion, dispute it with a reason, or create a revised draft version. A Manager/Reviewer demo role can request changes or record a human approval decision. Audit events and current-version insights are available in the UI.

This is a functional prototype of the core text-and-claims workflow, not a complete production brand-governance platform or legal compliance checker.

## 2. Core workflow delivered

1. **Configure:** seed rules and approved claims are available in the local ledger; a claim-creation form adds fictional test records.
2. **Submit:** a user enters draft text, intended channel and product scope.
3. **Run checks:** deterministic wording and claim checks execute in the FastAPI backend.
4. **Retrieve/cite evidence:** each actionable finding links to a source ID and human-readable stored source label.
5. **Show findings:** the UI shows excerpt, severity, explanation and suggested next step.
6. **Creator response:** a creator can acknowledge a suggestion, dispute it with a reason, or edit and rescan the text.
7. **Human approval:** a Manager/Reviewer demo role can request changes or approve. Open/disputed findings require an override rationale.
8. **Audit and improve:** revisions and actions are recorded. Disputes surface as guideline-gap signals in the insights page; no rule is edited automatically.

## 3. The three improvements represented in this build

| Improvement from the Round 1 design direction | Round 2 implementation | Evidence / limitation |
|---|---|---|
| **1. Approved-claims ledger with scope and expiry** | Claim records store exact wording, product/channel scope, source reference, approver and valid dates. Matching expired claims and scope mismatches are flagged. | CL-001, CL-002 and CL-003 are fictional seed records. Twenty-one labelled cases include current claim and scope cases. |
| **2. Citation-or-silence findings** | Findings include a stored rule or claims-record ID and source label. Unsupported comparisons cite BG-CLAIM-01; stale approvals cite the corresponding claim record and BG-CLAIM-02. | The automated suite checks that every generated finding contains a source ID and label. The underlying rules are a small fictional rule pack, not a full regulatory corpus. |
| **3. Human-controlled review with dispute-driven gap signals** | Creator acknowledgement/dispute, versioned edits, reviewer request-changes/approval, override rationale and audit history are implemented. Current-version disputes appear in insights. | Role checks are demonstrative only; there is no identity authentication. Insight clusters are counts, not semantic clustering. No guideline changes occur automatically. |

## 4. Technology and architecture

- **Backend/API:** Python 3.11+ and FastAPI.
- **Data:** SQLite for local persistence; it stores rules, claims, reviews, text versions, findings and audit events.
- **UI:** HTML, CSS and vanilla JavaScript served by the same FastAPI process.
- **Analysis:** deterministic regex-based checks and exact claim-ledger matching; no LLM is called.
- **Testing:** pytest, FastAPI TestClient and a 21-case JSON labelled draft set.
- **External APIs/models/datasets:** none used at runtime. Seed content and evidence labels are fictional. Standard open-source packages are listed in `requirements.txt`.

The original Round 1 plan listed React/Next.js, PostgreSQL + pgvector and a Claude API candidate. The prototype deliberately deviates to a simpler local stack to demonstrate an inspectable end-to-end workflow without API keys or external data transfer. It does not yet provide semantic retrieval or AI-generated tone analysis.

See `ARCHITECTURE.md` for a data-flow diagram and design decisions.

## 5. Test evidence

**Automated test run: 29 passed, 0 failed** with `python -m pytest -q` in the build environment on 28 October 2026.

- 21 labelled draft acceptance cases across unsupported superlatives/comparisons, expired claims, scope mismatch, guarantee/rapid-result wording, terminology and advisory tone checks.
- API/workflow tests cover health and seed data, source-linked findings, accepting a suggestion without silent editing, dispute reasons and audit events, role restrictions, approval override rationale, versioned editing/rescan, invalid claim dates, plus dashboard/claims/rules/insights and static UI responses.

This is software-test evidence only. It does not prove precision/recall on real marketing content, usability with external participants, reduced review times, or legal compliance. `TEST_RESULTS.md` includes the test command and interpretation.

## 6. User testing and structured feedback

No external user interviews, survey responses or moderated usability sessions are claimed. This is consistent with the Round 1 proposal's status, which marked interviews and survey as pending. `USER_TESTING_TEMPLATE.csv` is included to collect task completion, timing, confusing steps and feedback without collecting names or company-confidential material. Complete it with real participants before presenting it as user evidence.

## 7. Team contribution statements

The responsibility allocation below is copied from the Round 1 plan; it is **not evidence that each member completed that work in this generated package**. Replace it with actual work, code/commit evidence and a truthful individual statement before submission.

- **Kotha Siddhartha Raj:** Round 1 planned responsibility — claim verification and evaluation set; shared research, testing, documentation and demo.
- **Marupaka Durga Bhavani:** Round 1 planned responsibility — backend, database and workflow; shared research, testing, documentation and demo.
- **Panchagiri Akshitha:** Round 1 planned responsibility — frontend, UX and accessibility; shared research, testing, documentation and demo.

See `CONTRIBUTIONS.md` for a confirmation checklist. Disclose AI assistance as required by the organiser.

## 8. Privacy, security and responsible design

- All seed brands, claims and evidence labels are fictional.
- The demo stores draft text locally in an unencrypted SQLite file; do not upload confidential company copy.
- The role selector is a workflow demonstration, not login or production authorization. A caller can spoof the submitted role.
- This is a single-workspace application. Organization-level tenant isolation, secure authentication and deployment hardening are out of scope.
- Missing internal evidence is described as a missing approval record, not as proof of factual falsity.
- Findings are decision support. Human reviewers remain responsible for exceptions and final decisions.
- Tone detections are heuristic and advisory; accessibility, images, OCR and document parsing are not implemented.

## 9. Run and demonstration materials

The source package is installable locally on Windows with Python; see `README.md`. It does not require Node.js, API keys or a database server. Run the app at `http://127.0.0.1:8000`; the interactive API documentation is at `/docs`.

- Source + setup: `README.md`
- AI-use and runtime-service disclosure: `AI_DISCLOSURE.md`
- Architecture: `ARCHITECTURE.md`
- Demo steps: `DEMO_SCRIPT.md`
- Automated test evidence: `TEST_RESULTS.md`
- Contribution confirmation: `CONTRIBUTIONS.md`
- Real user feedback form: `USER_TESTING_TEMPLATE.csv`

## 10. Known limitations and next steps

1. Add real login and server-side authorization with organization-scoped access and encrypted storage before any cloud deployment.
2. Add automated parsing for DOCX/PDF and measurable asset/accessibility checks only after text workflow reliability is verified.
3. Introduce a versioned LLM provider adapter only after privacy/retention review; require structured output and verify citations against stored sources.
4. Expand the labelled dataset with human-adjudicated positive, negative and ambiguous cases; report precision, recall, false positives and false negatives.
5. Conduct moderated usability tests with actual creators/reviewers; report sample size and negative feedback honestly.
6. Publish to a public or judge-accessible repository and provide a live URL only after the team has reviewed the source, confirmed the allowed build window, and selected a hosting/authentication approach.

**Submission claim:** This package provides a working local text-review prototype with testable claim, citation, dispute and human-approval flows. It does not claim a public deployment, a production AI service, completed primary research or validated real-world impact.
