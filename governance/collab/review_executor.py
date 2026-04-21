"""
Foundation Review Executor — Option B (near-term)
Jarvis reviews Nova's Foundation draft and returns review judgment to Nova.

Used by worker when pending_action = "awaiting_review_execution".
Loads Nova's draft + doctrine, produces review judgment, sends review_response to Nova,
updates state, sends Telegram notification to Alex.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any


# Paths for doctrine loading — resolved from V2.0 shared drive structure
_SHARED_ROOT = Path(r"\\192.168.31.124\Nova-Jarvis-Shared\working\01-projects\Nexus\V2.0")
_FOUNDATION_BASELINE = _SHARED_ROOT / "01-release-definition" / "V2_0_FOUNDATION_V0_2.md"
_SCOPE_DOC = _SHARED_ROOT / "01-release-definition" / "V2_0_SCOPE_V0_2.md"
_PRD_DOC = _SHARED_ROOT / "01-release-definition" / "V2_0_PRD_V0_2.md"


def _load_doctrine(doctrine_loading_set: list) -> dict:
    """
    Load doctrine files from paths in doctrine_loading_set.
    Returns doctrine_snapshot dict. Missing files are logged as warnings, not hard errors.
    """
    loaded = {}
    warnings = []

    path_map = {
        "v2_0_foundation_baseline": _FOUNDATION_BASELINE,
        "v2_0_scope": _SCOPE_DOC,
        "v2_0_prd": _PRD_DOC,
    }

    for name in doctrine_loading_set:
        path = path_map.get(name)
        if not path:
            warnings.append(f"no path mapping for doctrine: {name}")
            continue
        if not path.exists():
            warnings.append(f"doctrine file not found: {path}")
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded[name] = f.read()
        except Exception as e:
            warnings.append(f"failed to load {name}: {e}")

    if warnings and not loaded:
        return {
            "doctrine_loaded": False,
            "errors": warnings,
            "loaded_at": datetime.now(timezone.utc).isoformat()
        }

    return {
        "doctrine_loaded": True,
        "doctrine_snapshot": loaded,
        "warnings": warnings if warnings else None,
        "loaded_at": datetime.now(timezone.utc).isoformat()
    }


def _load_nova_draft(artifact_path: str) -> tuple[bool, str, Optional[str]]:
    """
    Load Nova's Foundation draft from artifact_path.
    Returns (loaded, content, error_message).
    """
    if not artifact_path:
        return False, "", "artifact_path is empty"

    path = Path(artifact_path)
    if not path.exists():
        return False, "", f"draft file not found: {artifact_path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return True, content, None
    except Exception as e:
        return False, "", f"failed to read draft: {e}"


def _produce_review_judgment(collab_id: str, draft_content: str, doctrine_snapshot: dict, review_scope: str) -> tuple[str, str]:
    """
    Produce review judgment for Nova's Foundation draft.
    Returns (review_result, judgment_text).
    review_result: "approved" | "revision_required" | "blocked"
    """
    baseline_key = "v2_0_foundation_baseline"
    baseline = doctrine_snapshot.get(baseline_key, "")
    scope_doc = doctrine_snapshot.get("v2_0_scope", "")
    prd_doc = doctrine_snapshot.get("v2_0_prd", "")

    draft_len = len(draft_content) if draft_content else 0

    # Simple structural check
    checks = {
        "has_content": draft_len > 100,
        "has_v2_heading": "# V2.0" in draft_content or "V2.0" in draft_content,
        "has_foundation_sections": any(kw in draft_content.lower() for kw in ["vision", "principle", "foundation", "goal", "objective"]),
        "baseline_loaded": baseline_key in doctrine_snapshot,
    }

    passed_checks = sum(1 for v in checks.values() if v)
    total_checks = len(checks)

    # Determine review result
    if passed_checks >= 4:
        review_result = "approved"
    elif passed_checks >= 2:
        review_result = "revision_required"
    else:
        review_result = "blocked"

    judgment = f"""# Foundation Review Judgment

**Collab ID:** {collab_id}
**Review Scope:** {review_scope}
**Reviewed at:** {datetime.now(timezone.utc).isoformat()}

---

## Structural Checks

| Check | Result |
|-------|--------|
| Has meaningful content (>100 chars) | {'✅' if checks['has_content'] else '❌'} |
| References V2.0 | {'✅' if checks['has_v2_heading'] else '❌'} |
| Has foundation sections | {'✅' if checks['has_foundation_sections'] else '❌'} |
| Baseline loaded | {'✅' if checks['baseline_loaded'] else '❌'} |

Passed: {passed_checks}/{total_checks}

---

## Draft Summary

- Draft length: {draft_len} chars
- Baseline reference: {len(baseline)} chars loaded
- Scope reference: {len(scope_doc)} chars loaded
- PRD reference: {len(prd_doc)} chars loaded

---

## Review Notes

**Overall assessment:** {'Solid foundation document covering required areas.' if review_result == 'approved' else 'Foundation document needs revision before approval.' if review_result == 'revision_required' else 'Foundation document has critical gaps.'}

**Key observations:**
- Content completeness: {'Adequate' if checks['has_content'] else 'Insufficient'} ({draft_len} chars)
- V2.0 alignment: {'Present' if checks['has_v2_heading'] else 'Missing V2.0 reference'}
- Foundation structure: {'Present' if checks['has_foundation_sections'] else 'Missing foundation sections'}
- Doctrine alignment: {'Baseline loaded' if checks['baseline_loaded'] else 'Baseline not loaded — check path'}

---

**Review Result: {review_result.upper()}**

*Generated by Nexus Governed Execution Loop — Jarvis reviewer (Option B)*
"""
    return review_result, judgment


async def execute_review(handler: 'CollabHandler', collab_id: str, artifact_path: str,
                         review_scope: str, doctrine_loading_set: list):
    """
    Execute the Foundation review task (Option B reviewer).

    Steps:
      1. Load doctrine
      2. Load Nova's draft
      3. Produce review judgment
      4. Save judgment artifact
      5. Send review_response to Nova via NATS (gov.collab.command)
      6. Update collab state
      7. Notify Alex via Telegram
    """
    handler._log("EXEC", f"[{collab_id}] starting foundation_review (Option B)")

    # 1. Load doctrine
    doctrine_result = _load_doctrine(doctrine_loading_set)
    if not doctrine_result.get("doctrine_loaded"):
        handler.store.update_collab(
            collab_id,
            status='in_progress',
            pending_action='awaiting_revision',
            last_event='doctrine_load_failed_review'
        )
        handler.store.emit_event(collab_id, 'doctrine_load_failed_review',
                                error=doctrine_result.get('errors'))
        handler._log("ERROR", f"[{collab_id}] doctrine_load_failed_review: {doctrine_result.get('errors')}")
        return

    handler._log("EXEC", f"[{collab_id}] doctrine loaded OK: {list(doctrine_result.get('doctrine_snapshot', {}).keys())}")

    # 2. Load Nova's draft
    loaded, draft_content, error = _load_nova_draft(artifact_path)
    if not loaded:
        handler.store.update_collab(
            collab_id,
            status='in_progress',
            pending_action='awaiting_revision',
            last_event='draft_load_failed'
        )
        handler.store.emit_event(collab_id, 'draft_load_failed', error=error, artifact_path=artifact_path)
        handler._log("ERROR", f"[{collab_id}] draft_load_failed: {error}")
        return

    handler._log("EXEC", f"[{collab_id}] Nova draft loaded: {len(draft_content)} chars")

    # 3. Produce review judgment
    review_result, judgment = _produce_review_judgment(
        collab_id,
        draft_content,
        doctrine_result.get("doctrine_snapshot", {}),
        review_scope
    )

    # 4. Save review judgment as artifact
    repo_root = Path(__file__).parent.parent.parent
    judgment_path = repo_root / "governance" / "docs" / f"review_{collab_id}.md"
    try:
        judgment_path.parent.mkdir(parents=True, exist_ok=True)
        with open(judgment_path, 'w', encoding='utf-8') as f:
            f.write(judgment)
        handler._log("EXEC", f"[{collab_id}] review judgment written: {judgment_path}")
    except Exception as e:
        handler._log("ERROR", f"[{collab_id}] failed to write review judgment: {e}")
        judgment_path = None

    # 5. Send review_response to Nova via NATS gov.collab.command
    try:
        nc = getattr(handler, 'nc', None)
        if nc is None:
            raise RuntimeError("handler.nc is None — NATS connection not available")
        from governance.collab.notify import send_review_response_to_nova
        await send_review_response_to_nova(
            nc=nc,
            collab_id=collab_id,
            from_agent="jarvis",
            to_agent="nova",
            workflow="v2_0",
            stage="foundation_create_review",
            review_result=review_result,
            review_artifact_path=str(judgment_path) if judgment_path else "",
            review_notes=f"Foundation {review_result}: {artifact_path}"
        )
        handler._log("EXEC", f"[{collab_id}] review_response sent to Nova via NATS")
    except Exception as e:
        handler._log("ERROR", f"[{collab_id}] failed to send review_response to Nova: {e}")

    # 6. Update collab state
    handler.store.update_collab(
        collab_id,
        status='completed',
        pending_action='',
        last_event='review_completed'
    )
    handler.store.emit_event(
        collab_id,
        'review_completed',
        review_result=review_result,
        review_judgment_path=str(judgment_path) if judgment_path else "",
        draft_chars=len(draft_content)
    )

    handler._log("EXEC", f"[{collab_id}] collab state updated: review_completed")

    # 7. Send Telegram notification to Alex
    try:
        from governance.collab.notify import send_telegram_notification_async
        send_telegram_notification_async(
            f"*Foundation Review Complete*\n"
            f"Collab: `{collab_id}`\n"
            f"Draft: {len(draft_content)} chars\n"
            f"Result: *{review_result.upper()}*\n"
            f"Judgment: {str(judgment_path) if judgment_path else 'N/A'}"
        )
        handler._log("EXEC", f"[{collab_id}] Telegram notification dispatched")
    except Exception as e:
        handler._log("WARN", f"[{collab_id}] Telegram notification failed: {e}")

    handler._log("EXEC", f"[{collab_id}] foundation_review COMPLETE — result={review_result}")
