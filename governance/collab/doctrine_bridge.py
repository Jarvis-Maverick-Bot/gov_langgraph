"""
Doctrine Bridge — Runtime Contract Loader
========================================

Purpose: Turn doctrine files into runtime contracts AND structured context for AI reasoning.

Gap this fills:
- System has doctrine files but they don't drive runtime decisions
- This bridge provides both contract metadata AND model-usable context

Two-layer output:
1. load_doctrine_snapshot() → LoadedDoctrine (for contract metadata)
2. build_doctrine_context() → DoctrineContext (for AI model reasoning)

Files read from:
  \\\\192.168.31.124\\Nova-Jarvis-Shared\\working\\01-projects\\Nexus\\V2.0\\
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ── Path configuration helpers ──────────────────────────────────────────────────

def _load_config() -> dict:
    config_path = Path(__file__).parent / "collab_config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _get_effective_roots() -> Tuple[Path, Path]:
    """
    Returns (effective_local_root, effective_transport_root).
    Rule: effective_local = local_shared_root ?? transport_shared_root
          effective_transport = transport_shared_root ?? local_shared_root
    Raises ValueError if both are None.
    """
    config = _load_config()
    paths_cfg = config.get("paths", {})
    local_root = paths_cfg.get("local_shared_root")
    transport_root = paths_cfg.get("transport_shared_root")
    if local_root is None and transport_root is None:
        raise ValueError(
            "collab_config.json paths.local_shared_root and paths.transport_shared_root "
            "are both null — at least one must be set"
        )
    effective_local = Path(local_root) if local_root else Path(transport_root)
    effective_transport = Path(transport_root) if transport_root else Path(local_root)
    return effective_local, effective_transport


def _doctrine_base_path() -> Path:
    """Return the V2.0 project root for doctrine loading (effective_local + project_rel_root)."""
    effective_local, _ = _get_effective_roots()
    config = _load_config()
    rel_root = config.get("paths", {}).get("project_rel_root", "")
    if rel_root:
        return effective_local / rel_root
    return effective_local


# ── Doctrine name → file path mapping ────────────────────────────────────────

_DOCTRINE_BASE = None  # lazy-initialized


def _get_doctrine_base() -> Path:
    global _DOCTRINE_BASE
    if _DOCTRINE_BASE is None:
        _DOCTRINE_BASE = _doctrine_base_path()
    return _DOCTRINE_BASE


def DOCTRINE_PATHS() -> Dict[str, Path]:
    """Returns doctrine name → full path dict, built from current config."""
    base = _get_doctrine_base()
    release_def = base / "01-release-definition"
    return {
        "v2_0_foundation_baseline": release_def / "V2_0_FOUNDATION_V0_2.md",
        "v2_0_scope":               release_def / "V2_0_SCOPE_V0_2.md",
        "v2_0_prd":                 release_def / "V2_0_PRD_V0_2.md",
    }


# ── Layer 1: Doctrine Snapshot (contract metadata source) ─────────────────────

@dataclass
class DoctrineSnapshot:
    """Structured doctrine context for runtime use."""
    name: str
    content: str
    path: Path
    loaded: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class LoadedDoctrine:
    """Union of all doctrine snapshots for a given loading set."""
    doctrine_snapshot: Dict[str, DoctrineSnapshot]
    doctrine_loaded: bool
    errors: List[str]


def load_doctrine_snapshot(doctrine_loading_set: List[str]) -> LoadedDoctrine:
    """
    Load all doctrine files named in doctrine_loading_set.
    Returns a LoadedDoctrine with all snapshots + success/failure per file.

    Usage:
        result = load_doctrine_snapshot(["v2_0_foundation_baseline", "v2_0_scope", "v2_0_prd"])
        if result.doctrine_loaded:
            snapshot = result.doctrine_snapshot
    """
    errors = []
    doctrine_snapshot = {}

    for name in doctrine_loading_set:
        path = DOCTRINE_PATHS().get(name)
        if not path:
            errors.append(f"no path mapping for doctrine: {name}")
            doctrine_snapshot[name] = DoctrineSnapshot(
                name=name, content="", path=path or Path(), loaded=False, errors=["no path mapping"]
            )
            continue

        if not path.exists():
            workspace_path = Path(__file__).parent.parent.parent / "governance" / "docs" / path.name
            if workspace_path.exists():
                path = workspace_path

        try:
            content = path.read_text(encoding='utf-8')
            doctrine_snapshot[name] = DoctrineSnapshot(
                name=name, content=content, path=path, loaded=True, errors=[]
            )
        except FileNotFoundError:
            doctrine_snapshot[name] = DoctrineSnapshot(
                name=name, content="", path=path, loaded=False, errors=[f"file not found: {path}"]
            )
            errors.append(f"file not found: {path}")
        except Exception as e:
            doctrine_snapshot[name] = DoctrineSnapshot(
                name=name, content="", path=path, loaded=False, errors=[str(e)]
            )
            errors.append(f"error loading {name}: {e}")

    doctrine_loaded = all(s.loaded for s in doctrine_snapshot.values())

    return LoadedDoctrine(
        doctrine_snapshot=doctrine_snapshot,
        doctrine_loaded=doctrine_loaded,
        errors=errors
    )


# ── Layer 2: DoctrineContext (for AI model reasoning) ──────────────────────────

@dataclass
class DoctrineContext:
    """
    结构化 doctrine context，给模型推理用。

    包含：
    - workflow/stage 元数据
    - 从文件抽取的关键段落（供模型快速理解）
    - 完整原始内容（供模型查证）
    - loaded 状态和 errors（降级路径用）
    """
    workflow: str
    stage: str
    scope_summary: str                          # 从 scope 抽的摘要
    baseline_expectations: List[str]           # foundation 关键要求列表
    prd_requirements: List[str]                # PRD 关键需求列表
    doctrine_files: Dict[str, str]             # name → raw content（完整原文）
    loaded: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _extract_list_items(content: str, section_pattern: str) -> List[str]:
    """
    从 markdown 内容中抽取列表项。
    简单正则：不依赖模型，纯文本解析。
    """
    items = []
    # Find section
    match = re.search(section_pattern, content, re.IGNORECASE | re.MULTILINE)
    if not match:
        return items
    section_start = match.end()
    # Find next heading or end
    remaining = content[section_start:]
    next_heading = re.search(r'\n##?\s', remaining)
    section_content = remaining[:next_heading.start() if next_heading else len(remaining)]
    # Extract list items (- or * or numbered)
    for line in section_content.split('\n'):
        stripped = line.strip()
        if stripped.startswith(('- ', '* ')) or re.match(r'^\d+\.\s', stripped):
            items.append(re.sub(r'^[\-\*\d.]+\s+', '', stripped).strip())
    return items


def _extract_summary(content: str, max_chars: int = 400) -> str:
    """从文件开头抽取摘要。"""
    # Skip frontmatter and headers
    text = re.sub(r'^---[\s\S]*?---\n', '', content)
    text = re.sub(r'^#.*\n', '', text, count=1)
    text = text.strip()
    return text[:max_chars] + ('...' if len(text) > max_chars else '')


def build_doctrine_context(
    doctrine_loading_set: List[str],
    workflow: str,
    stage: str
) -> DoctrineContext:
    """
    把 doctrine 文件转换成模型可用的结构化 context。

    Step 1: load_doctrine_snapshot() 加载原始文件
    Step 2: 对每个文件做轻量解析（正则抽标题/列表/关键段落）
    Step 3: 打包成 DoctrineContext

    降级路径：
    - 文件不存在 → loaded=False，errors 记录，context 仍返回（允许降级判断）
    - 部分文件缺失 → loaded=False，warnings 记录，其他文件仍可用
    """
    loaded_result = load_doctrine_snapshot(doctrine_loading_set)
    doctrine_files = {}
    errors = list(loaded_result.errors)
    warnings = []
    unavailable_doctrines = set()

    for name, snapshot in loaded_result.doctrine_snapshot.items():
        if snapshot.loaded:
            doctrine_files[name] = snapshot.content
        else:
            doctrine_files[name] = ""
            unavailable_doctrines.add(name)

    # Parse scope
    scope_content = loaded_result.doctrine_snapshot.get("v2_0_scope", None)
    scope_summary = ""
    if scope_content and scope_content.loaded:
        scope_summary = _extract_summary(scope_content.content, max_chars=400)
    else:
        warnings.append("v2_0_scope not available — summary unavailable")

    # Parse foundation baseline expectations
    foundation_content = loaded_result.doctrine_snapshot.get("v2_0_foundation_baseline", None)
    baseline_expectations = []
    if foundation_content and foundation_content.loaded:
        baseline_expectations = _extract_list_items(
            foundation_content.content,
            r'(?:^|\n)##?\s*(?:Requirements?|Key Requirements?|Baseline Requirements?)'
        )
    else:
        warnings.append("v2_0_foundation_baseline not available")

    # Parse PRD requirements
    prd_content = loaded_result.doctrine_snapshot.get("v2_0_prd", None)
    prd_requirements = []
    if prd_content and prd_content.loaded:
        prd_requirements = _extract_list_items(
            prd_content.content,
            r'(?:^|\n)##?\s*(?:Requirements?|Functional Requirements?)'
        )
    else:
        warnings.append("v2_0_prd not available")

    return DoctrineContext(
        workflow=workflow,
        stage=stage,
        scope_summary=scope_summary,
        baseline_expectations=baseline_expectations,
        prd_requirements=prd_requirements,
        doctrine_files=doctrine_files,
        loaded=loaded_result.doctrine_loaded,
        errors=errors,
        warnings=warnings
    )


# ── Contract-driven executor helpers ────────────────────────────────────────────

from .runtime_contract_map import get_contract, StepContract, NotifyPolicy


def get_mandatory_output(message_type: str) -> Optional[str]:
    """Return the mandatory_output for a message type, or None if terminal."""
    contract = get_contract(message_type)
    return contract.mandatory_output if contract else None


def get_allowed_results(message_type: str) -> List[str]:
    """Return allowed_results for a message type."""
    contract = get_contract(message_type)
    return contract.allowed_results if contract else []


def get_executor(message_type: str) -> Optional[str]:
    """Return which agent should handle this message type."""
    contract = get_contract(message_type)
    return contract.executor if contract else None


def get_notify_policy(message_type: str) -> List[NotifyPolicy]:
    """Return notify policy for a message type."""
    contract = get_contract(message_type)
    return contract.notify_policy if contract else []


# ── Re-exports ─────────────────────────────────────────────────────────────────

__all__ = [
    "load_doctrine_snapshot",
    "build_doctrine_context",
    "get_contract",
    "get_mandatory_output",
    "get_allowed_results",
    "get_executor",
    "get_notify_policy",
    "LoadedDoctrine",
    "DoctrineSnapshot",
    "DoctrineContext",
    "DOCTRINE_PATHS",
]