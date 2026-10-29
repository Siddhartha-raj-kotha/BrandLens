# BrandLens — Test Results

**Test date:** 28 October 2026  
**Command:** `python -m pytest -q`  
**Result:** `29 passed` (0 failures; current run completed in approximately 1 second in the build environment).

## Coverage

- 21 labelled draft cases in `tests/acceptance_cases.json`:
  - Unsupported No.1 / number-one / #1 / best / leading claims.
  - Unapproved comparative and percentage claims.
  - Expired approved claim record.
  - Product-scope mismatch against an otherwise current approved claim.
  - Absolute guarantee and rapid-result wording.
  - Advisory tone heuristic for all-caps/repeated exclamation marks.
  - Preferred terminology and clean text examples.
- API and workflow tests:
  - Health endpoint and demo seed review.
  - Source ID and source label are present on generated findings.
  - Accepting a suggestion leaves draft text unchanged.
  - Dispute requires a reason and is stored in the audit trail.
  - Creator cannot approve; reviewer approval with open findings requires a rationale.
  - Editing creates a new version and reruns checks.
  - Claim date validation rejects an end date before the start date.
  - Static UI, dashboard, claims, rules and insights endpoints return data.

## Interpretation and limits

These tests verify specific programmed examples and workflow behavior. They do **not** measure production precision/recall, guarantee that every claim risk is detected, prove rule completeness, establish legal compliance, or count as external user testing. A human should review the expected outcome for each added case before extending the test set. The source data are fictional; evidence IDs such as DEMO-003 are not external sources.
