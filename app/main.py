from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DB_PATH = Path(os.getenv("BRANDLENS_DB_PATH", str(BASE_DIR / "data" / "brandlens.db")))
TODAY = date.today().isoformat()

@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(
    title="BrandLens",
    description="Source-grounded, human-controlled pre-publication brand governance MVP.",
    version="0.2.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def rowdict(row):
    return dict(row) if row is not None else None


def init_db() -> None:
    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                rule_text TEXT NOT NULL,
                source_name TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                claim TEXT NOT NULL,
                product_scope TEXT NOT NULL,
                channel_scope TEXT NOT NULL,
                evidence_source TEXT NOT NULL,
                approver TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_until TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                product_scope TEXT NOT NULL DEFAULT 'Not specified',
                status TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS review_versions (
                review_id TEXT NOT NULL,
                version_no INTEGER NOT NULL,
                draft_text TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (review_id, version_no),
                FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                review_id TEXT NOT NULL,
                version_no INTEGER NOT NULL,
                rule_id TEXT,
                claim_id TEXT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                explanation TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_label TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                dispute_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (review_id, version_no) REFERENCES review_versions(review_id, version_no) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT,
                version_no INTEGER,
                actor TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        # Lightweight schema migration for a pre-existing local demo database.
        review_columns = {row[1] for row in conn.execute("PRAGMA table_info(reviews)")}
        if "product_scope" not in review_columns:
            conn.execute("ALTER TABLE reviews ADD COLUMN product_scope TEXT NOT NULL DEFAULT 'Not specified'")

        if conn.execute("SELECT COUNT(*) FROM rules").fetchone()[0] == 0:
            rules = [
                ("BG-CLAIM-01", "Claims need scoped evidence", "Claims", "high",
                 "Comparative, quantified and superlative promotional claims must match a current approved claim record with product and channel scope.",
                 "Fictional Brand Guide", "v1.2", "active"),
                ("BG-TERM-01", "Avoid absolute guarantees", "Terminology", "high",
                 "Avoid absolute guarantee language unless a current approved record explicitly supports the exact promise.",
                 "Fictional Brand Guide", "v1.2", "active"),
                ("BG-TONE-01", "Use calm, plain language", "Tone", "low",
                 "Use clear, calm language; avoid shouting through all-caps words and repeated exclamation marks.",
                 "Fictional Brand Guide", "v1.2", "active"),
                ("BG-TERM-02", "Prefer customer-first terminology", "Terminology", "low",
                 "For public-facing copy, prefer 'customers' over the internal term 'users' when referring to buyers.",
                 "Fictional Brand Guide", "v1.2", "active"),
                ("BG-CLAIM-02", "Time-limited facts must be current", "Claims", "high",
                 "A fact or performance claim must not be used after its approved validity end date.",
                 "Claims Governance Policy", "v1.0", "active"),
            ]
            conn.executemany("INSERT INTO rules VALUES (?,?,?,?,?,?,?,?)", rules)

        if conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0:
            claims = [
                ("CL-001", "Hydration support for up to 8 hours.", "LumaSkin Hydration Gel", "Social / Web",
                 "Fictional evidence memo DEMO-001 (seed data; not an external source)", "Demo reviewer",
                 "2026-01-01", "2027-01-31", "approved", "Scope limited to LumaSkin Hydration Gel."),
                ("CL-002", "Contains 1% fictional ingredient X.", "LumaSkin Serum", "Web / Email",
                 "Fictional lab summary DEMO-002 (seed data; not an external source)", "Demo reviewer",
                 "2026-01-01", "2027-12-31", "approved", "Fictional ingredient and evidence for demonstration only."),
                ("CL-003", "40% more effective than leading brands.", "LumaSkin Serum", "Social / Web",
                 "Fictional comparative study DEMO-003 (seed data; not an external source)", "Demo reviewer",
                 "2025-01-01", "2026-06-30", "expired", "Expired before the demo date; must not be treated as current approval."),
            ]
            conn.executemany("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?)", claims)

        # Seed one completed sample review only on a fresh database, to make the dashboard useful immediately.
        if conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0:
            draft = ("India's No.1 skincare brand, with guaranteed results in one day. "
                     "Our serum is 40% more effective than leading brands!!!")
            review_id = "BL-DEMO-001"
            stamp = now_iso()
            conn.execute(
                "INSERT INTO reviews(id,title,channel,product_scope,status,created_by,created_at,updated_at,current_version) VALUES (?,?,?,?,?,?,?,?,1)",
                (review_id, "Launch campaign — demo draft", "Instagram / Social", "LumaSkin Serum", "needs_review", "Demo creator", stamp, stamp),
            )
            conn.execute(
                "INSERT INTO review_versions(review_id,version_no,draft_text,created_by,created_at) VALUES (?,?,?,?,?)",
                (review_id, 1, draft, "Demo creator", stamp),
            )
            findings = analyze_draft(draft, conn, date.today())
            for item in findings:
                conn.execute(
                    """INSERT INTO findings(id,review_id,version_no,rule_id,claim_id,title,category,severity,excerpt,
                       explanation,source_id,source_label,suggestion,status,dispute_reason,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'open','',?)""",
                    (str(uuid4()), review_id, 1, item["rule_id"], item["claim_id"], item["title"], item["category"],
                     item["severity"], item["excerpt"], item["explanation"], item["source_id"], item["source_label"],
                     item["suggestion"], stamp),
                )
            conn.execute(
                "INSERT INTO audit_events(review_id,version_no,actor,actor_role,event_type,detail,created_at) VALUES (?,?,?,?,?,?,?)",
                (review_id, 1, "Demo creator", "Creator", "submitted", "Demo review seeded with fictional test content.", stamp),
            )


def load_rules(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    return {row["id"]: row for row in conn.execute("SELECT * FROM rules WHERE status='active'")}


def load_claims(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM claims ORDER BY id"))


def _normalized(s: str) -> str:
    return re.sub(r"\s+", " ", s.casefold()).strip()


def _claim_phrase(s: str) -> str:
    # Ignore punctuation differences (e.g. a period in the ledger vs !!! in draft copy).
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def _claim_is_present(claim: str, text: str) -> bool:
    phrase = _claim_phrase(claim)
    return bool(phrase) and phrase in _claim_phrase(text)


def _scope_matches(approved_scope: str, requested_scope: str, kind: str) -> bool:
    approved = (approved_scope or "").strip().casefold()
    requested = (requested_scope or "").strip().casefold()
    all_labels = {"all", "all products", "all channels", "*", "general"}
    if approved in all_labels:
        return True
    if not requested or requested == "not specified":
        return False
    if kind == "product":
        return approved == requested
    approved_parts = [part.strip() for part in re.split(r"[/,;|]", approved) if part.strip()]
    requested_parts = [part.strip() for part in re.split(r"[/,;|]", requested) if part.strip()]
    return any(a == r or a in r or r in a for a in approved_parts for r in requested_parts)


def analyze_draft(text: str, conn: sqlite3.Connection, today: date | None = None, product_scope: str = "LumaSkin Serum", channel: str = "Instagram / Social") -> list[dict]:
    """Deterministic demo checks. Each finding cites a specific seed rule or claim record."""
    today = today or date.today()
    lower = text.casefold()
    claims = load_claims(conn)
    findings: list[dict] = []

    def add(title, category, severity, excerpt, explanation, source_id, source_label, suggestion, rule_id=None, claim_id=None):
        findings.append({
            "rule_id": rule_id,
            "claim_id": claim_id,
            "title": title,
            "category": category,
            "severity": severity,
            "excerpt": excerpt[:240],
            "explanation": explanation,
            "source_id": source_id,
            "source_label": source_label,
            "suggestion": suggestion,
        })

    # Exact claim-ledger matches are checked for date and scope. A missing record is not treated as proof of falsity.
    recognized_claim_spans: list[tuple[int, int, str]] = []
    for claim in claims:
        if _claim_is_present(claim["claim"], text):
            phrase = claim["claim"].strip().rstrip(".!?")
            span_match = re.search(re.escape(phrase), text, re.I)
            if span_match:
                recognized_claim_spans.append((span_match.start(), span_match.end(), claim["id"]))
            start = date.fromisoformat(claim["valid_from"])
            end = date.fromisoformat(claim["valid_until"])
            product_ok = _scope_matches(claim["product_scope"], product_scope, "product")
            channel_ok = _scope_matches(claim["channel_scope"], channel, "channel")
            source_label = f"{claim['id']} · {claim['claim']} · scope: {claim['product_scope']} / {claim['channel_scope']} · valid to {claim['valid_until']}"
            if claim["status"] == "expired" or end < today:
                add(
                    "Claim approval expired", "Claims", "high", claim["claim"],
                    f"The matching record {claim['id']} expired on {claim['valid_until']}. This flags stale approval, not factual falsity.",
                    claim["id"], source_label,
                    "Remove the claim or obtain a renewed, scoped approval before using it.",
                    rule_id="BG-CLAIM-02", claim_id=claim["id"],
                )
            elif start > today or claim["status"] != "approved":
                add(
                    "Claim is not currently approved", "Claims", "high", claim["claim"],
                    f"The matching record {claim['id']} is not in its approved validity period ({claim['valid_from']} to {claim['valid_until']}).",
                    claim["id"], source_label,
                    "Wait for approval to become effective or obtain a current approval record.",
                    rule_id="BG-CLAIM-02", claim_id=claim["id"],
                )
            elif not product_ok or not channel_ok:
                mismatches = []
                if not product_ok:
                    mismatches.append(f"product scope '{claim['product_scope']}' does not match '{product_scope}'")
                if not channel_ok:
                    mismatches.append(f"channel scope '{claim['channel_scope']}' does not match '{channel}'")
                add(
                    "Approved claim scope does not match", "Claims", "high", claim["claim"],
                    f"The wording exists in {claim['id']}, but " + " and ".join(mismatches) + ". Approval is limited to its recorded scope.",
                    claim["id"], source_label,
                    "Use the claim only within the approved scope or obtain a reviewer-approved record for this product and channel.",
                    rule_id="BG-CLAIM-01", claim_id=claim["id"],
                )

    # Comparative/superlative claim: exact guideline citation remains available even where no claim record exists.
    patterns = [
        re.compile(r"(?:\b(?:no\s*\.?\s*1|number\s+one|best(?:-in-class)?|india'?s\s+leading)\b|#\s*1\b)", re.I),
        re.compile(r"\b(?:more effective than|better than|outperform(?:s|ing)?)\b", re.I),
        re.compile(r"\b\d+(?:\.\d+)?\s?%\s*(?:more|better|less|higher|lower|effective)?\b", re.I),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            excerpt = match.group(0)
            # Do not duplicate claim-specific findings for text already matched to a ledger record.
            if any(start <= match.start() and match.end() <= end for start, end, _claim_id in recognized_claim_spans):
                continue
            add(
                "Promotional claim needs an approved record", "Claims", "high", excerpt,
                "The wording makes a comparative, quantified or superlative claim, but this draft does not contain an exact current approved record for this assertion. Missing internal evidence does not by itself prove the claim is false.",
                "BG-CLAIM-01", f"BG-CLAIM-01 · Claims need scoped evidence · Fictional Brand Guide v1.2",
                "Remove the superlative/comparison or link a current approved record with evidence, product scope, channel and validity dates.",
                rule_id="BG-CLAIM-01",
            )

    # Absolute guarantee / rapid-result language.
    for match in re.finditer(r"\b(?:guarantee(?:d|s)?|miracle|instant(?:ly)?|results?\s+in\s+one\s+day|overnight results?)\b", text, re.I):
        add(
            "Absolute or rapid-result wording", "Terminology", "high", match.group(0),
            "The brand guide asks for absolute promises to be avoided unless the exact promise has current approved evidence.",
            "BG-TERM-01", "BG-TERM-01 · Avoid absolute guarantees · Fictional Brand Guide v1.2",
            "Describe a measurable, substantiated benefit without an absolute guarantee or rapid-result promise.",
            rule_id="BG-TERM-01",
        )

    # Tone check is explicitly advisory: it does not evaluate brand identity or legal compliance.
    caps = re.findall(r"\b[A-Z]{4,}\b", text)
    exclamations = re.search(r"!{2,}", text)
    if caps or exclamations:
        excerpt = caps[0] if caps else exclamations.group(0)
        add(
            "Tone may read as shouting", "Tone", "low", excerpt,
            "A simple style heuristic found all-caps wording or repeated exclamation marks. This is advisory and context-sensitive.",
            "BG-TONE-01", "BG-TONE-01 · Use calm, plain language · Fictional Brand Guide v1.2",
            "Try sentence case and one clear statement; a human reviewer should judge the intended emphasis.",
            rule_id="BG-TONE-01",
        )

    if re.search(r"\busers\b", text, re.I):
        add(
            "Check customer-first terminology", "Terminology", "low", re.search(r"\busers\b", text, re.I).group(0),
            "The fictional style guide prefers 'customers' in public-facing copy when referring to buyers.",
            "BG-TERM-02", "BG-TERM-02 · Prefer customer-first terminology · Fictional Brand Guide v1.2",
            "Consider replacing 'users' with 'customers' where the text refers to buyers.",
            rule_id="BG-TERM-02",
        )

    # De-duplicate repeated same-rule same-excerpt matches while preserving distinct claims.
    unique = []
    seen = set()
    for item in findings:
        key = (item["title"], item["excerpt"].casefold(), item["source_id"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


class ReviewCreate(BaseModel):
    title: str = Field(default="Untitled review", max_length=120)
    channel: str = Field(default="Social post", max_length=80)
    product_scope: str = Field(default="Not specified", max_length=120)
    draft_text: str = Field(min_length=5, max_length=20000)
    created_by: str = Field(default="Demo creator", max_length=80)
    actor_role: Literal["Creator", "Manager", "Reviewer", "Admin"] = "Creator"


class ActionRequest(BaseModel):
    action: Literal["accept", "dispute", "edit", "approve", "request_changes"]
    actor: str = Field(default="Demo user", max_length=80)
    actor_role: Literal["Creator", "Manager", "Reviewer", "Admin"] = "Creator"
    finding_id: str | None = None
    reason: str = Field(default="", max_length=1000)
    draft_text: str | None = Field(default=None, max_length=20000)


class ClaimCreate(BaseModel):
    claim: str = Field(min_length=5, max_length=500)
    product_scope: str = Field(min_length=2, max_length=120)
    channel_scope: str = Field(default="All channels", max_length=120)
    evidence_source: str = Field(min_length=3, max_length=300)
    approver: str = Field(default="Demo reviewer", max_length=80)
    valid_from: str
    valid_until: str
    note: str = Field(default="", max_length=500)
    actor_role: Literal["Creator", "Manager", "Reviewer", "Admin"] = "Creator"


def audit(conn, review_id, version_no, actor, actor_role, event_type, detail):
    conn.execute(
        "INSERT INTO audit_events(review_id,version_no,actor,actor_role,event_type,detail,created_at) VALUES (?,?,?,?,?,?,?)",
        (review_id, version_no, actor, actor_role, event_type, detail, now_iso()),
    )


def save_findings(conn, review_id: str, version_no: int, draft_text: str, product_scope: str = "LumaSkin Serum", channel: str = "Instagram / Social"):
    items = analyze_draft(draft_text, conn, product_scope=product_scope, channel=channel)
    stamp = now_iso()
    for item in items:
        conn.execute(
            """INSERT INTO findings(id,review_id,version_no,rule_id,claim_id,title,category,severity,excerpt,
               explanation,source_id,source_label,suggestion,status,dispute_reason,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'open','',?)""",
            (str(uuid4()), review_id, version_no, item["rule_id"], item["claim_id"], item["title"], item["category"],
             item["severity"], item["excerpt"], item["explanation"], item["source_id"], item["source_label"],
             item["suggestion"], stamp),
        )
    return items


def review_payload(conn, review_row):
    review = dict(review_row)
    version = conn.execute(
        "SELECT * FROM review_versions WHERE review_id=? AND version_no=?",
        (review["id"], review["current_version"]),
    ).fetchone()
    review["draft_text"] = version["draft_text"] if version else ""
    review["findings"] = [dict(r) for r in conn.execute(
        "SELECT * FROM findings WHERE review_id=? AND version_no=? ORDER BY CASE severity WHEN 'high' THEN 0 ELSE 1 END, created_at",
        (review["id"], review["current_version"]),
    )]
    review["versions"] = [dict(r) for r in conn.execute(
        "SELECT version_no,created_by,created_at FROM review_versions WHERE review_id=? ORDER BY version_no DESC",
        (review["id"],),
    )]
    review["open_findings"] = sum(1 for f in review["findings"] if f["status"] in ("open", "disputed"))
    return review


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "BrandLens", "version": app.version, "date": date.today().isoformat()}


@app.get("/api/dashboard")
def dashboard():
    with db_conn() as conn:
        reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM reviews WHERE status IN ('needs_review','changes_requested','disputed')").fetchone()[0]
        open_findings = conn.execute("SELECT COUNT(*) FROM findings f JOIN reviews r ON r.id=f.review_id AND r.current_version=f.version_no WHERE f.status IN ('open','disputed')").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM reviews WHERE status='approved'").fetchone()[0]
        recent = [review_payload(conn, row) for row in conn.execute("SELECT * FROM reviews ORDER BY updated_at DESC LIMIT 5")]
        return {"reviews": reviews, "pending": pending, "open_findings": open_findings, "approved": approved, "recent": recent}


@app.get("/api/reviews")
def list_reviews():
    with db_conn() as conn:
        return [review_payload(conn, row) for row in conn.execute("SELECT * FROM reviews ORDER BY updated_at DESC")]


@app.post("/api/reviews", status_code=201)
def create_review(payload: ReviewCreate):
    if payload.actor_role not in ("Creator", "Admin"):
        raise HTTPException(403, "Only the Creator or Admin demo role can submit a new draft.")
    review_id = f"BL-{uuid4().hex[:8].upper()}"
    stamp = now_iso()
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO reviews(id,title,channel,product_scope,status,created_by,created_at,updated_at,current_version) VALUES (?,?,?,?,?,?,?,?,1)",
            (review_id, payload.title.strip() or "Untitled review", payload.channel, payload.product_scope, "needs_review", payload.created_by, stamp, stamp),
        )
        conn.execute(
            "INSERT INTO review_versions(review_id,version_no,draft_text,created_by,created_at) VALUES (?,?,?,?,?)",
            (review_id, 1, payload.draft_text, payload.created_by, stamp),
        )
        findings = save_findings(conn, review_id, 1, payload.draft_text, payload.product_scope, payload.channel)
        audit(conn, review_id, 1, payload.created_by, payload.actor_role, "submitted", f"Draft submitted and scanned; {len(findings)} finding(s) created.")
        return review_payload(conn, conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone())


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Review not found")
        return review_payload(conn, row)


@app.post("/api/reviews/{review_id}/actions")
def review_action(review_id: str, payload: ActionRequest):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Review not found")
        current_version = row["current_version"]
        role = payload.actor_role
        action = payload.action
        if action in ("edit", "accept", "dispute") and role not in ("Creator", "Admin"):
            raise HTTPException(403, f"{role} cannot perform this creator action in the demo workflow.")
        if action in ("approve", "request_changes") and role not in ("Manager", "Reviewer", "Admin"):
            raise HTTPException(403, "Only a Manager, Reviewer or Admin can make this approval decision.")

        stamp = now_iso()
        if action == "edit":
            if payload.draft_text is None or len(payload.draft_text.strip()) < 5:
                raise HTTPException(422, "Revised draft must contain at least 5 characters.")
            next_version = current_version + 1
            conn.execute(
                "INSERT INTO review_versions(review_id,version_no,draft_text,created_by,created_at) VALUES (?,?,?,?,?)",
                (review_id, next_version, payload.draft_text, payload.actor, stamp),
            )
            conn.execute("UPDATE reviews SET current_version=?,status='needs_review',updated_at=? WHERE id=?", (next_version, stamp, review_id))
            items = save_findings(conn, review_id, next_version, payload.draft_text, row["product_scope"], row["channel"])
            audit(conn, review_id, next_version, payload.actor, role, "revision", f"Draft revised and rescanned; {len(items)} finding(s) in version {next_version}.")
        elif action in ("accept", "dispute"):
            if not payload.finding_id:
                raise HTTPException(422, "finding_id is required for this action.")
            finding = conn.execute("SELECT * FROM findings WHERE id=? AND review_id=? AND version_no=?", (payload.finding_id, review_id, current_version)).fetchone()
            if not finding:
                raise HTTPException(404, "Finding not found in the current version.")
            if action == "dispute" and not payload.reason.strip():
                raise HTTPException(422, "A short reason is required to dispute a finding.")
            if action == "accept":
                conn.execute("UPDATE findings SET status='accepted' WHERE id=?", (payload.finding_id,))
                detail = f"Accepted suggestion for finding {finding['id']} ({finding['title']}); draft text was not silently changed."
                event = "finding_accepted"
            else:
                conn.execute("UPDATE findings SET status='disputed',dispute_reason=? WHERE id=?", (payload.reason.strip(), payload.finding_id))
                conn.execute("UPDATE reviews SET status='disputed',updated_at=? WHERE id=?", (stamp, review_id))
                detail = f"Disputed finding {finding['id']} ({finding['title']}): {payload.reason.strip()}"
                event = "finding_disputed"
            audit(conn, review_id, current_version, payload.actor, role, event, detail)
            conn.execute("UPDATE reviews SET updated_at=? WHERE id=?", (stamp, review_id))
        elif action == "approve":
            open_count = conn.execute("SELECT COUNT(*) FROM findings WHERE review_id=? AND version_no=? AND status IN ('open','disputed')", (review_id, current_version)).fetchone()[0]
            if open_count and not payload.reason.strip():
                raise HTTPException(409, "Open or disputed findings remain. Resolve them or enter an override rationale to record the human decision.")
            conn.execute("UPDATE reviews SET status='approved',updated_at=? WHERE id=?", (stamp, review_id))
            audit(conn, review_id, current_version, payload.actor, role, "approved", f"Human approval recorded. {('Override rationale: ' + payload.reason.strip()) if payload.reason.strip() else 'No outstanding findings.'}")
        elif action == "request_changes":
            reason = payload.reason.strip() or "Reviewer requested changes."
            conn.execute("UPDATE reviews SET status='changes_requested',updated_at=? WHERE id=?", (stamp, review_id))
            audit(conn, review_id, current_version, payload.actor, role, "changes_requested", reason)
        return review_payload(conn, conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone())


@app.get("/api/rules")
def list_rules():
    with db_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM rules ORDER BY category,id")]


@app.get("/api/claims")
def list_claims():
    today = date.today().isoformat()
    with db_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM claims ORDER BY valid_until DESC")]
    for item in rows:
        item["is_current"] = item["status"] == "approved" and item["valid_from"] <= today <= item["valid_until"]
    return rows


@app.post("/api/claims", status_code=201)
def create_claim(payload: ClaimCreate):
    if payload.actor_role != "Admin":
        raise HTTPException(403, "Only the Admin demo role can add an approved claim record.")
    try:
        start = date.fromisoformat(payload.valid_from)
        end = date.fromisoformat(payload.valid_until)
    except ValueError:
        raise HTTPException(422, "Dates must use YYYY-MM-DD format.")
    if end < start:
        raise HTTPException(422, "valid_until must be on or after valid_from.")
    claim_id = f"CL-{uuid4().hex[:6].upper()}"
    status = "approved" if start <= date.today() <= end else ("expired" if end < date.today() else "pending")
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?)",
            (claim_id, payload.claim.strip(), payload.product_scope.strip(), payload.channel_scope.strip(),
             payload.evidence_source.strip(), payload.approver.strip(), start.isoformat(), end.isoformat(), status, payload.note.strip()),
        )
        return rowdict(conn.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone())


@app.get("/api/insights")
def insights():
    with db_conn() as conn:
        groups = [dict(r) for r in conn.execute(
            """SELECT f.source_id, f.title, f.category, COUNT(*) AS count,
                      SUM(CASE WHEN f.status='disputed' THEN 1 ELSE 0 END) AS disputed
               FROM findings f JOIN reviews r ON r.id=f.review_id AND r.current_version=f.version_no
               GROUP BY f.source_id,f.title,f.category ORDER BY count DESC, disputed DESC"""
        )]
        disputed = [dict(r) for r in conn.execute(
            """SELECT f.id,f.title,f.source_id,f.dispute_reason,f.created_at,r.title AS review_title
               FROM findings f JOIN reviews r ON r.id=f.review_id AND r.current_version=f.version_no
               WHERE f.status='disputed' ORDER BY f.created_at DESC LIMIT 10"""
        )]
        audit_rows = [dict(r) for r in conn.execute("SELECT * FROM audit_events ORDER BY created_at DESC, id DESC LIMIT 15")]
        totals = conn.execute("SELECT COUNT(*) FROM findings f JOIN reviews r ON r.id=f.review_id AND r.current_version=f.version_no").fetchone()[0]
        return {"rule_clusters": groups, "disputes": disputed, "audit": audit_rows, "findings_total": totals}


@app.get("/api/reviews/{review_id}/audit")
def review_audit(review_id: str):
    with db_conn() as conn:
        exists = conn.execute("SELECT 1 FROM reviews WHERE id=?", (review_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Review not found")
        return [dict(r) for r in conn.execute("SELECT * FROM audit_events WHERE review_id=? ORDER BY id DESC", (review_id,))]


@app.post("/api/demo/reset")
def demo_reset():
    """Explicitly reset demo data. Meant for local demos only."""
    with db_conn() as conn:
        conn.execute("DELETE FROM audit_events")
        conn.execute("DELETE FROM findings")
        conn.execute("DELETE FROM review_versions")
        conn.execute("DELETE FROM reviews")
        conn.execute("DELETE FROM claims")
        conn.execute("DELETE FROM rules")
    init_db()
    return {"status": "reset", "message": "Local demo seed data restored."}
