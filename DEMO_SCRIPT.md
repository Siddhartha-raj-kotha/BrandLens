# BrandLens — 4-minute Round 2 Demo Script

**Use only fictional seed content.** Suggested presenter: one member drives the UI; other members explain their confirmed contributions. The exact recorded actions should be performed live, not described as already completed if they have not been.

## 0:00–0:30 — Explain the problem

“BrandLens is a pre-publication review layer. Our key choice is not to let an AI silently approve content. It links findings to stored rules and claim records, then leaves decisions with people.”

Mention that all current product/claim records in the workspace are fictional.

## 0:30–1:20 — Inspect a risky draft

1. Open the Overview page and click **Launch campaign — demo draft**.
2. Point out “No.1”, “guaranteed results in one day”, “40% more effective” and the repeated exclamation marks.
3. Open the findings and read the exact source ID: the “No.1” flag cites `BG-CLAIM-01`; the comparative claim cites expired record `CL-003` / `BG-CLAIM-02`; absolute language cites `BG-TERM-01`.
4. Explain that a missing record is not proof the statement is false; it means the claim is not approved in this demo ledger.

## 1:20–2:10 — Prove the ledger checks scope and dates

1. Open **Claims ledger**.
2. Show CL-003 with its 30 June 2026 validity end date and “Expired” status.
3. Switch the demo role to **Admin** to add a clearly fictional test claim, or point to CL-001's product/channel scope.
4. Explain that the engine checks exact text, status, validity and matching product/channel scope; it is not a general-purpose truth engine.

## 2:10–3:05 — Show human control

1. Return to the review as **Creator**.
2. Dispute one finding and enter a reason.
3. Show the audit event and the dispute signal in **Insights & audit**.
4. Change the demo role to **Reviewer** and request changes or approve with an override rationale. Explain that this role switch simulates a workflow and is not a secure login.

## 3:05–3:40 — Show version history

1. Switch back to **Creator**.
2. Edit the draft to remove unsupported language; click **Save revision & rescan**.
3. Explain that a new version is created and findings are recalculated. The previous text version and the revision event remain recorded.

## 3:40–4:00 — Test evidence and limits

Show that the automated suite passes 28 tests, including a 21-case labelled test set. State explicitly that these are software tests on fictional examples; external user testing and live-world performance measurement are pending. Mention that no external LLM is integrated in this version.
