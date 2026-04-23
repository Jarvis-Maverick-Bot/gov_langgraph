"""
TC2 — Review Executor Smoke Test

Tests only the review phase using an existing Foundation draft.
Does NOT test protocol/NATS — only the LLM review output quality.

Input: \\192.168.31.124\...\V2_0_FOUNDATION.md (UNC accessible from Jarvis)
Output: structured review_response with verdict/reasons/required_changes
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure governance package is resolvable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from governance.collab.review_executor import execute_review
from governance.collab.state_store import CollabStateStore


ARTIFACT_PATH = (
    "\\\\192.168.31.124\\Nova-Jarvis-Shared\\working\\01-projects\\Nexus\\V2.0\\"
    "governance\\docs\\V2_0_FOUNDATION.md"
)


class _MockStore:
    """Minimal state store mock for execute_review — no-op state ops."""
    def __init__(self):
        self.updated = []

    def get_collab(self, collab_id):
        class _C:
            review_round = 0
        return _C()

    def update_collab(self, collab_id, **kw):
        self.updated.append(kw)
        return True

    def emit_event(self, *a, **kw):
        pass


class _MockHandler:
    """Minimal handler mock for execute_review."""
    def __init__(self):
        self.store = _MockStore()
        self.log_lines = []

    def _log(self, level, msg):
        entry = f"[{level}] {msg}"
        self.log_lines.append(entry)
        print(entry)


async def main():
    print("=" * 60)
    print("TC2 — Review Executor Smoke Test")
    print("=" * 60)

    handler = _MockHandler()
    collab_id = "tc2-test-001"
    artifact_path = ARTIFACT_PATH
    review_scope = "foundation_review"
    doctrine_loading_set = [
        "v2_0_foundation_baseline",
        "v2_0_scope",
        "v2_0_prd",
    ]

    # Step 1: Check draft is readable
    p = Path(artifact_path)
    print(f"\n[1] Checking draft at:\n    {artifact_path}")
    if p.exists():
        size = p.stat().st_size
        print(f"[OK] Draft exists — {size} bytes")
    else:
        print(f"[FAIL] Draft not found")
        return

    # Step 2: Execute review
    print(f"\n[2] Calling execute_review() ...")
    result = await execute_review(
        handler=handler,
        collab_id=collab_id,
        artifact_path=artifact_path,
        review_scope=review_scope,
        doctrine_loading_set=doctrine_loading_set,
    )

    # Step 3: Validate result fields
    print(f"\n[3] Validating review result ...")
    required_fields = {
        "message_type": str,
        "collab_id": str,
        "result": str,
        "reasons": str,
        "required_changes": str,
    }
    allowed_results = {"approved", "revision_required", "blocked", "review_execution_error"}

    all_ok = True
    for field, expected_type in required_fields.items():
        val = getattr(result, field, None)
        if val is None:
            print(f"  [FAIL] '{field}' is None/missing")
            all_ok = False
        elif not isinstance(val, expected_type):
            print(f"  [FAIL] '{field}' type={type(val).__name__}, expected {expected_type.__name__}")
            all_ok = False
        else:
            preview = repr(val[:80]) if isinstance(val, str) else val
            print(f"  [OK]   {field} = {preview}")

    # Step 4: Check result value
    verdict = getattr(result, "result", None)
    print(f"\n[4] Verdict check: {verdict}")
    if verdict in allowed_results:
        print(f"  [OK] verdict '{verdict}' is in allowed set")
    else:
        print(f"  [FAIL] verdict '{verdict}' not in {allowed_results}")
        all_ok = False

    # Step 5: Non-empty reasons check
    reasons = getattr(result, "reasons", None) or ""
    if len(reasons) >= 10:
        print(f"  [OK] reasons is substantive ({len(reasons)} chars)")
    else:
        print(f"  [FAIL] reasons too short ({len(reasons)} chars)")

    print(f"\n{'=' * 60}")
    if all_ok:
        print("TC2 PASS — review executor produced valid structured output")
    else:
        print("TC2 FAIL — see above")
    print(f"{'=' * 60}\n")

    return all_ok


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
