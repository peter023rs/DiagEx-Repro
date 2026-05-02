"""Phase 1 scoring kinds from spec §9.1 + plan §4.1.

Each scorer takes ``(expected, actual, params, graph)`` and returns a
:class:`ScoreResult`. ``graph`` is the predicted ``ReconciledGraph`` (used by
``graph_reachability``); other scorers ignore it.

The scorers are deliberately pure and dependency-light: input is plain
Python types loaded from yaml/json, output is a dataclass with a 0/1 score
plus a free-form ``detail`` string for the report. No LLM calls, no
filesystem access — that keeps cassette mode honest.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from diagex.vision.models import ReconciledEdge, ReconciledGraph, ReconciledNode

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreResult:
    score: float            # 1.0 = correct, 0.0 = wrong; intermediate allowed
    kind: str               # mirrors the scoring kind from queries.truth.yaml
    detail: str             # one-line explanation for the report

    @property
    def correct(self) -> bool:
        return self.score >= 1.0


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


_WS = re.compile(r"\s+")
_TAG_NORM = re.compile(r"[^a-z0-9]+")
# Pulls a leading tag-shaped substring (e.g. "XV-2151", "E-234-009", "SP-1106A")
# out of a verbose label like "XV-2151 (shutdown valve, left feed-gas inlet)" or
# "Sea Water Strainer SP-1106A". Used to relax label matching when the LLM
# decorates the bare tag with a description.
_TAG_ROOT = re.compile(r"\b([A-Z]{1,4}[-/][A-Z0-9\-/]*\d[A-Z0-9\-/]*)\b")


def _norm(s: str, *, case_sensitive: bool = False, normalize: bool = True) -> str:
    out = s if case_sensitive else s.lower()
    if normalize:
        out = _WS.sub(" ", out).strip()
    return out


def _norm_tag(s: str, *, case_sensitive: bool = False) -> str:
    """Tag normalisation: lower, drop punctuation/whitespace.

    Mirrors the OPC normalisation in spec §5.5 — uppercased there because OPC
    labels are stored uppercase, but for query scoring we lower before strip
    so case-insensitive set-match works the same way."""
    out = s if case_sensitive else s.lower()
    out = _TAG_NORM.sub("", out)
    return out


def _tag_root(s: str) -> str:
    """Extract a leading tag-shaped substring from a verbose label.

    "XV-2151 (shutdown valve, left feed-gas inlet)" -> "xv2151"
    "Sea Water Strainer SP-1106A" -> "sp1106a"
    Returns the empty string if no tag-shaped token is present.
    """
    if not s:
        return ""
    m = _TAG_ROOT.search(s)
    return _norm_tag(m.group(1)) if m else ""


def _labels_share_root(a: str, b: str) -> bool:
    """True when labels share a non-empty extracted tag-root."""
    ra, rb = _tag_root(a), _tag_root(b)
    return bool(ra) and ra == rb


# Leading "OPC" markers used by some truth conventions, e.g.
# "OPC IN: Spent Butane ...", "OPC-OUT-MNb47121", "OPC-IN MN".
_OPC_PREFIX = re.compile(
    r"^\s*opc[\s\-_:]*(?:in|out)?[\s\-_:]*",
    re.IGNORECASE,
)
# Direction / preposition words to strip from anywhere in the label.
_OPC_DROP_WORDS = re.compile(
    r"\b(inlet|outlet|in|out|to|from)\b",
    re.IGNORECASE,
)


def _opc_alpha_tokens(s: str, *, min_len: int = 3) -> list[str]:
    """Tokens used for OPC identity comparison.

    Procedure:
      1. Strip a leading ``OPC[-/_/:/space](IN|OUT)?`` marker.
      2. Drop parenthetical qualifiers (``CWS (Condenser)`` -> ``CWS``).
      3. Drop direction / preposition words (``to``, ``from``, ``inlet``,
         ``outlet``, ``in``, ``out``).
      4. Return alphanumeric tokens of length >= ``min_len`` (lowercased).

    Examples:
      "OPC IN: Spent Butane from V-234"  -> ["spent","butane","234"]
      "OPC-IN-MNb47121"                  -> ["mnb47121"]
      "Feed A inlet"                     -> ["feed"]
      "MNb inlet"                        -> ["mnb"]
    """
    if not s:
        return []
    work = _OPC_PREFIX.sub("", s)
    work = re.sub(r"\([^)]*\)", " ", work)
    work = _OPC_DROP_WORDS.sub(" ", work)
    raw = re.findall(r"[A-Za-z0-9]+", work)
    return [t.lower() for t in raw if len(t) >= min_len]


def _opc_label_match(a: str, b: str, *, min_len: int = 3) -> bool:
    """Loose label match for OPCs (off-page connectors).

    Truth and prediction use widely-divergent conventions across fixtures:
      * "Feed A inlet"        (textbook style: identifier + direction)
      * "OPC IN: Spent Butane from V-234-002A~D (P-234-03016-F3D-8\"-Is)"
                              (customer style: marker + descriptor + line tag)
      * "OPC-IN-MNb47121"     (synthetic / DEXPI-XML style: id-encoded)

    They are matched by extracting alphanumeric identity tokens (after
    stripping the OPC marker, direction words, and parenthetical qualifiers)
    and checking whether either label's first identity token appears in the
    other's token set or is its prefix. This catches "MNb" ⊂ "MNb47121" and
    "Spent Butane" tokens shared with truth.
    """
    ta = _opc_alpha_tokens(a, min_len=min_len)
    tb = _opc_alpha_tokens(b, min_len=min_len)
    if not ta or not tb:
        return False
    set_a, set_b = set(ta), set(tb)
    # Direct token overlap is sufficient.
    if set_a & set_b:
        return True
    # Prefix relation on the leading tokens (handles MNb ↔ MNb47121).
    head_a, head_b = ta[0], tb[0]
    if head_a.startswith(head_b) or head_b.startswith(head_a):
        return min(len(head_a), len(head_b)) >= min_len
    return False


# ---------------------------------------------------------------------------
# Actual-answer extraction from a Phase 1 run result
# ---------------------------------------------------------------------------


# Lines whose first whitespace-separated word (lower, depunctuated) is one of
# these are treated as prose preamble and dropped. The set covers the common
# leak patterns we've seen ("Confirmed: …", "Answer: …", "Based on …", "All
# visible MOVs are identified, …", etc.). Single-word lines are not affected
# (the check requires ≥ 2 words on the line).
_PROSE_PREFIXES = frozenset({
    "answer", "result", "results", "summary", "total", "count", "recap",
    "confirmed", "identified", "verified", "found", "located", "noted",
    "observed", "checked", "complete", "completed",
    "based", "looking", "considering", "given",
    "the", "these", "those", "this", "all", "both", "any", "each",
    "here", "below", "above",
    "additionally", "furthermore", "moreover", "however",
    "i", "we", "they", "it",
})


# Tokens whose presence on a line marks it as a sentence/phrase rather than a
# bare-tag list. If any of these appear as a separate whitespace-separated
# word (after stripping punctuation) the whole line is dropped. Bare-tag
# lists never contain English connectors, so this is safe.
_PROSE_CONNECTORS = frozenset({
    "and", "or", "but", "nor", "yet", "so",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had",
    "with", "from", "of", "in", "on", "at", "by", "for", "as",
    "i", "we", "they", "it", "this", "that", "these", "those",
    "not", "no", "yes",
    "shown", "visible", "located", "found", "seen", "see", "show",
    "confirmed", "identified", "appears", "appear",
    "all", "both", "any", "each", "every", "some",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "however", "additionally", "furthermore", "moreover",
})


def _is_prose_preamble(line: str) -> bool:
    parts = line.split(maxsplit=1)
    if len(parts) < 2:
        return False
    first = parts[0].strip(".,;:!?\"'").lower()
    return first in _PROSE_PREFIXES


def _has_prose_connector(line: str) -> bool:
    for tok in line.split():
        norm = tok.strip(".,;:!?\"'()[]").lower()
        if norm in _PROSE_CONNECTORS:
            return True
    return False


_ANSWER_BLOCK_RE = re.compile(
    r"<answer>\s*(.*?)\s*</answer>", re.DOTALL | re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"^`{3,}\s*\w*\s*$")
# Single-letter / single-digit label prefix: "A: V-1001", "1: P-101".
# Stripped per-piece after comma split. Two-or-more-character prefixes are
# left alone (less likely to be question-borrowed labels, more likely tags).
_SINGLE_CHAR_LABEL_PREFIX_RE = re.compile(r"^[A-Za-z0-9]\s*:\s+")


def parse_list_answer(answer_text: str) -> list[str]:
    """Pull a list of items out of a free-text answer.

    Phase 1 returns a single ``answer`` string per page. Inventory queries are
    set-matched, so the harness needs to lift the items out. Heuristic: split
    on newlines + ``,`` / ``;`` and bullets, then strip leading list markers
    and trailing punctuation. Lines ending with ``:`` are dropped (header-
    shaped, e.g. ``"Pumps:"``); lines beginning with a known prose word
    (``"Confirmed: ..."``, ``"Based on ..."``, ``"All visible ..."``) are
    dropped to keep reasoning leaks out of the set. Empty lines are dropped.
    The caller is expected to apply ``_norm_tag`` for set comparison.

    Three model-style accommodations:
      * If an ``<answer>...</answer>`` block is present, parse only its
        contents — model wrapped its bare-tag list in an XML envelope.
      * Triple-backtick code fences (``` ``` ```, ``` ```python ```) are
        dropped as items.
      * Per-piece, a leading ``"X: "`` prefix where X is a single letter or
        digit is stripped — handles "A: V-1001, D: V-1002" (model echoing
        the question's stream / index labels) without over-stripping
        multi-character prefixes that may belong to tags.
    """
    block = _ANSWER_BLOCK_RE.search(answer_text)
    if block:
        answer_text = block.group(1)
    items: list[str] = []
    for raw_line in answer_text.splitlines():
        line0 = raw_line.strip()
        if not line0 or line0.endswith(":") or _is_prose_preamble(line0):
            continue
        if _CODE_FENCE_RE.match(line0):
            continue
        # Sentence-shaped lines (with English connectors like "and", "are",
        # "shown") are dropped — even if they happen to mention valid tags,
        # they tend to also mention rejected ones (e.g. "PSV-2152 and PSV-2153
        # confirmed. PSE-2151/2154 are not PSVs."). The bare-tag list that
        # follows in compliant answers is what we want.
        if _has_prose_connector(line0):
            continue
        # Comma / semicolon-separated tags on a single line are common despite
        # "one per line" instructions; split them out so each tag is its own item.
        for piece in re.split(r"[,;]", line0):
            line = piece.strip()
            if not line:
                continue
            # Strip bullet / numbered prefixes like "- ", "* ", "1. ", "1) ".
            line = re.sub(r"^([\-\*•]|\d+[\.\)])\s+", "", line)
            # Strip a single-character labelled prefix ("A: ", "1: ").
            line = _SINGLE_CHAR_LABEL_PREFIX_RE.sub("", line)
            # Drop trailing punctuation typical in prose ("FIC-102.").
            line = line.rstrip(".,;:")
            if line:
                items.append(line)
    return items


def parse_int_answer(answer_text: str) -> int | None:
    """Extract a single integer from a free-text answer.

    Strict prompts ask the model for a bare integer on its own line. With
    models that still emit a one-paragraph justification first, the literal
    answer ends up on the last line. This parser:

    1. Prefers a line whose stripped content is exactly an integer ("4" /
       "-3"); if multiple, takes the last (the verdict).
    2. Falls back to the first integer in the full text — but a leading ``-``
       is treated as negation only when not adjacent to a letter/digit, so
       hyphens inside identifiers like ``TT-001`` don't become "-1".
    """
    lone: list[int] = []
    for line in answer_text.splitlines():
        s = line.strip()
        if re.fullmatch(r"-?\d+", s):
            lone.append(int(s))
    if lone:
        return lone[-1]
    for m in re.finditer(r"-?\d+", answer_text):
        val = m.group(0)
        if val.startswith("-") and m.start() > 0:
            prev = answer_text[m.start() - 1]
            if prev.isalpha() or prev.isdigit():
                val = val[1:]
        return int(val)
    return None


_BOOL_TRUE = {"yes", "true", "y", "t", "1"}
_BOOL_FALSE = {"no", "false", "n", "f", "0"}


# ---------------------------------------------------------------------------
# Format suffixes — appended to a query's question by the harness so the
# model emits answers the parsers above can actually parse. The system being
# evaluated is unchanged; only the final-answer rendering is constrained.
# ---------------------------------------------------------------------------


_FORMAT_SUFFIX_BY_KIND: dict[str, str] = {
    "list": (
        "Output format: a newline-separated list of bare tag identifiers, "
        "nothing else. Example:\n"
        "  P-101\n"
        "  P-102\n"
        "Do NOT include introductions, completeness assertions, confirmations, "
        "summaries, sentences, parenthetical asides, items you considered and "
        "rejected, or any other prose. The final answer must consist "
        "exclusively of identifier tokens — one per line, one tag each. "
        "Lines containing English words (e.g. 'and', 'or', 'I', 'are', "
        "'shown', 'confirmed') are forbidden in the answer block — even if "
        "they also mention valid tags. If you wrote a prose sentence with the "
        "answer earlier, the answer block must still be ONLY bare tags. "
        "(Your internal reasoning is unaffected; only the final answer is "
        "constrained.)"
    ),
    "integer": (
        "Output format: a single integer on its own line, nothing else. "
        "Example:\n"
        "  7\n"
        "Do NOT include any prose, units, qualifiers, or restatements of the "
        "question. The final answer must contain only the digits (with an "
        "optional leading minus sign). "
        "(Your internal reasoning is unaffected; only the final answer is "
        "constrained.)"
    ),
    "boolean": (
        "Output format: exactly one word — 'yes' or 'no' — on its own line, "
        "nothing else. Example:\n"
        "  yes\n"
        "Do NOT include any prose, qualifiers, or explanations. The final "
        "answer must be a single word. "
        "(Your internal reasoning is unaffected; only the final answer is "
        "constrained.)"
    ),
    "string": (
        "Output format: the shortest possible noun phrase naming the "
        "equipment kind, nothing else. Example:\n"
        "  pump\n"
        "Use the most specific kind that fits (e.g., 'pressurizer' rather "
        "than the generic 'vessel'; 'centrifugal pump' only if the "
        "specialisation is unambiguous, otherwise 'pump'). "
        "Do NOT include any prose, hedging, location descriptions, or "
        "alternative interpretations. If nothing is at the location, answer "
        "exactly 'none'. "
        "(Your internal reasoning is unaffected; only the final answer is "
        "constrained.)"
    ),
}


def format_suffix(expected_kind: str) -> str:
    """Suffix to append to a Phase-1 question for the given ``expected_kind``.

    Returns an empty string for unknown kinds (no constraint imposed).
    """
    return _FORMAT_SUFFIX_BY_KIND.get(expected_kind.lower(), "")


# ---------------------------------------------------------------------------
# Coordinate-frame hint — appended to questions that mention "page
# coordinates". The truth files author coordinates in PDF points (top-left
# origin), but the agent's tool docs describe page-coordinate *pixels* of
# the rendered raster — so without this hint the model interprets q4 coords
# in the wrong frame and answers about a different region of the page.
# ---------------------------------------------------------------------------


_COORD_RE = re.compile(r"page coordinates", re.IGNORECASE)


def coord_frame_hint(page_size_pts: tuple[int, int] | None) -> str:
    """Hint clarifying that q4 coordinates are PDF points, not page pixels.

    If ``page_size_pts`` is provided, the page dimensions are included so the
    model can map between point space and the rendered raster it sees.
    """
    base = (
        "Note: page coordinates are in PDF points (1 pt = 1/72 inch), with "
        "top-left origin and y-down (Acrobat ruler convention). They are "
        "NOT page-pixel coordinates of the rendered raster you see — convert "
        "as needed by inferring the render scale from the visible image."
    )
    if page_size_pts:
        w, h = page_size_pts
        return base + f" The page is {int(w)} × {int(h)} pt."
    return base


def needs_coord_frame_hint(question: str) -> bool:
    return bool(_COORD_RE.search(question))


def parse_bool_answer(answer_text: str) -> bool | None:
    """Coerce a free-text yes/no answer to a bool.

    Order of checks: first word, last word, prefix ``yes``/``no``. The
    last-word check catches the common "reasoning paragraph + verdict at
    end" pattern that strict prompts don't always suppress.
    """
    flat = answer_text.strip().lower()
    if not flat:
        return None

    def _classify(tok: str) -> bool | None:
        tok = tok.strip(".,;:!?\"'")
        if tok in _BOOL_TRUE:
            return True
        if tok in _BOOL_FALSE:
            return False
        return None

    parts = flat.split()
    if parts:
        v = _classify(parts[0])
        if v is not None:
            return v
        v = _classify(parts[-1])
        if v is not None:
            return v
    if flat.startswith("yes"):
        return True
    if flat.startswith("no"):
        return False
    return None


# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------


def score_exact(expected: Any, actual: Any, params: dict[str, Any] | None = None) -> ScoreResult:
    case_sensitive = bool((params or {}).get("case_sensitive", False))
    e = expected if isinstance(expected, str) else str(expected)
    a = actual if isinstance(actual, str) else str(actual)
    e_n = _norm(e, case_sensitive=case_sensitive)
    a_n = _norm(a, case_sensitive=case_sensitive)
    return ScoreResult(
        score=1.0 if e_n == a_n else 0.0,
        kind="exact",
        detail=f"expected={e_n!r}, actual={a_n!r}",
    )


def score_contains(expected: Any, actual: Any, params: dict[str, Any] | None = None) -> ScoreResult:
    p = params or {}
    case_sensitive = bool(p.get("case_sensitive", False))
    normalize = bool(p.get("normalize", True))
    e = _norm(str(expected), case_sensitive=case_sensitive, normalize=normalize)
    a = _norm(str(actual), case_sensitive=case_sensitive, normalize=normalize)
    return ScoreResult(
        score=1.0 if e in a else 0.0,
        kind="contains",
        detail=f"needle={e!r} in {a!r}: {e in a}",
    )


def score_set_match(
    expected: Iterable[str],
    actual: Iterable[str],
    params: dict[str, Any] | None = None,
) -> ScoreResult:
    """F1 over normalised tag sets.

    Scoring is reported as the F1 score (0..1). The query is "correct" when
    F1 == 1.0, i.e. precision and recall both 1.0 — that is the rubric the
    paper's macro accuracy rolls up.
    """
    p = params or {}
    case_sensitive = bool(p.get("case_sensitive", False))
    exp_set = {_norm_tag(s, case_sensitive=case_sensitive) for s in expected if s}
    act_set = {_norm_tag(s, case_sensitive=case_sensitive) for s in actual if s}
    if not exp_set and not act_set:
        return ScoreResult(score=1.0, kind="set_match", detail="both empty")
    tp = len(exp_set & act_set)
    fp = len(act_set - exp_set)
    fn = len(exp_set - act_set)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return ScoreResult(
        score=f1,
        kind="set_match",
        detail=f"P={precision:.2f} R={recall:.2f} F1={f1:.2f} tp={tp} fp={fp} fn={fn}",
    )


def score_numeric_tolerance(
    expected: Any, actual: Any, params: dict[str, Any] | None = None,
) -> ScoreResult:
    """Spec §9.1: |pred - truth| / truth ≤ tolerance_frac (default 5%)."""
    p = params or {}
    tol = float(p.get("tolerance_frac", 0.05))
    try:
        e = float(expected)
        a = float(actual)
    except (TypeError, ValueError):
        return ScoreResult(score=0.0, kind="numeric_tolerance",
                           detail=f"non-numeric: expected={expected!r} actual={actual!r}")
    if e == 0:
        ok = a == 0
        return ScoreResult(score=1.0 if ok else 0.0, kind="numeric_tolerance",
                           detail=f"truth=0; pred={a}")
    rel = abs(a - e) / abs(e)
    return ScoreResult(
        score=1.0 if rel <= tol else 0.0,
        kind="numeric_tolerance",
        detail=f"truth={e} pred={a} rel_err={rel:.3f} tol={tol}",
    )


# ---- graph_reachability ----------------------------------------------------


def _label_match(label: str, target: str) -> bool:
    return _norm_tag(label) == _norm_tag(target)


def _resolve_node_id(graph: ReconciledGraph, target: str) -> str | None:
    """Find a node whose label matches ``target`` after normalisation."""
    for node in graph.nodes:
        if _label_match(node.label, target):
            return node.id
    return None


def _reachable(
    graph: ReconciledGraph,
    src_id: str,
    dst_id: str,
    line_types: set[str] | None,
) -> bool:
    """Undirected reachability over ``line_types`` (or all if None)."""
    adj: dict[str, set[str]] = {}
    for edge in graph.edges:
        if line_types is not None and edge.line_type not in line_types:
            continue
        adj.setdefault(edge.from_node, set()).add(edge.to_node)
        adj.setdefault(edge.to_node, set()).add(edge.from_node)
    if src_id not in adj:
        return src_id == dst_id
    seen = {src_id}
    stack = [src_id]
    while stack:
        cur = stack.pop()
        if cur == dst_id:
            return True
        for nbr in adj.get(cur, ()):
            if nbr not in seen:
                seen.add(nbr)
                stack.append(nbr)
    return False


_CONNECTIVITY_RE = re.compile(
    r"from\s+(?:`)?(?P<src>[A-Za-z0-9._\-/ ]+?)(?:`)?\s+to\s+(?:`)?(?P<dst>[A-Za-z0-9._\-/ ]+?)(?:`)?\s*\??\s*$",
    re.IGNORECASE,
)


def parse_connectivity_endpoints(question: str) -> tuple[str, str] | None:
    """Pull (src, dst) out of "Is there a process flow path from X to Y?".

    Returns None if the pattern doesn't match. Authors sometimes wrap tags in
    backticks; the regex strips them. Whitespace/casing is left to the
    label-matcher downstream.
    """
    m = _CONNECTIVITY_RE.search(question)
    if not m:
        return None
    return m.group("src").strip(), m.group("dst").strip()


def score_graph_reachability(
    expected: bool,
    actual: bool | None,
    params: dict[str, Any] | None = None,
    *,
    graph: ReconciledGraph | None = None,
    question: str | None = None,
) -> ScoreResult:
    """Boolean reachability scoring with two paths.

    1. If the harness produced a parsed boolean from the model's free-text
       answer, just compare it (``actual`` is True/False).
    2. Otherwise, fall back to deriving reachability from ``graph`` —
       endpoints come from ``question`` text. This lets us grade even when
       the model dodged the yes/no by listing edges instead.
    """
    expected_bool = bool(expected)
    if actual is None and graph is not None and question is not None:
        endpoints = parse_connectivity_endpoints(question)
        if endpoints is not None:
            src, dst = endpoints
            src_id = _resolve_node_id(graph, src)
            dst_id = _resolve_node_id(graph, dst)
            if src_id is None or dst_id is None:
                return ScoreResult(
                    score=0.0,
                    kind="graph_reachability",
                    detail=f"endpoint not found in graph (src={src!r} dst={dst!r})",
                )
            line_types_param = (params or {}).get("line_types")
            line_types = set(line_types_param) if line_types_param else None
            actual = _reachable(graph, src_id, dst_id, line_types)

    if actual is None:
        return ScoreResult(score=0.0, kind="graph_reachability",
                           detail="no boolean recoverable from answer or graph")
    score = 1.0 if bool(actual) == expected_bool else 0.0
    return ScoreResult(score=score, kind="graph_reachability",
                       detail=f"expected={expected_bool} actual={bool(actual)}")


# ---------------------------------------------------------------------------
# Top-level dispatcher
# ---------------------------------------------------------------------------


KIND_TO_SCORER = {
    "exact": score_exact,
    "contains": score_contains,
    "set_match": score_set_match,
    "numeric_tolerance": score_numeric_tolerance,
    "graph_reachability": score_graph_reachability,
}


def score_query(
    *,
    scoring: str,
    expected: Any,
    actual: Any,
    params: dict[str, Any] | None,
    graph: ReconciledGraph | None = None,
    question: str | None = None,
) -> ScoreResult:
    """Grade one query result against truth. Raises on unknown scoring."""
    if scoring == "graph_reachability":
        return score_graph_reachability(
            expected, actual, params, graph=graph, question=question,
        )
    if scoring not in KIND_TO_SCORER:
        raise ValueError(f"unknown scoring kind: {scoring!r}")
    return KIND_TO_SCORER[scoring](expected, actual, params)


# ---------------------------------------------------------------------------
# Phase 2 graph metrics (node / edge F1, tag OCR)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PRF:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


def _prf(tp: int, fp: int, fn: int) -> PRF:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return PRF(precision=p, recall=r, f1=f, tp=tp, fp=fp, fn=fn)


def _bbox_iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.w, a.y + a.h
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.w, b.y + b.h
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union > 0 else 0.0


def _node_match(tn: ReconciledNode, pn: ReconciledNode,
                iou: float, iou_threshold: float) -> bool:
    """Match rule used by node_f1 and edge_f1.

    Matches when same-kind nodes satisfy *any* of:
      * IoU ≥ threshold (spatial overlap),
      * normalised labels equal (e.g. ``XV-2151`` == ``XV-2151``),
      * extracted tag-roots equal — handles verbose LLM labels like
        ``XV-2151 (shutdown valve, left feed-gas inlet)`` matching the
        bare-tag truth ``XV-2151``,
      * for kind == "opc" only, the loose first-token match handles
        directional-suffix disagreement (``Feed A inlet`` ↔ ``Feed A``).
    """
    if iou >= iou_threshold:
        return True
    if tn.label and _norm_tag(tn.label) == _norm_tag(pn.label):
        return True
    if _labels_share_root(tn.label, pn.label):
        return True
    if tn.kind == "opc" and pn.kind == "opc" and _opc_label_match(tn.label, pn.label):
        return True
    return False


def node_f1(
    truth: list[ReconciledNode],
    pred: list[ReconciledNode],
    *,
    iou_threshold: float = 0.30,
    kind_filter: set[str] | None = None,
) -> PRF:
    """Spec §9.1: node match if same kind AND a match rule succeeds.

    Match rules: IoU ≥ threshold, equal normalised labels, equal extracted
    tag-roots, or (for OPC kind) loose first-token equality. Greedy 1-1
    matching — every truth node pairs with at most one prediction.
    """
    t_filtered = [n for n in truth if kind_filter is None or n.kind in kind_filter]
    p_filtered = [n for n in pred  if kind_filter is None or n.kind in kind_filter]
    used: set[int] = set()
    tp = 0
    for tn in t_filtered:
        # Match priority (descending):
        #   3 — exact-normalised label equality
        #   2 — verbose label sharing the same tag root
        #   1 — OPC loose first-token / token-overlap match
        #   0 — IoU-only (no label signal, just spatial overlap above threshold)
        # Within a priority tier, prefer higher IoU.
        best_idx = -1
        best_score = (-1, -1.0)
        for j, pn in enumerate(p_filtered):
            if j in used or pn.kind != tn.kind:
                continue
            iou = _bbox_iou(tn.bbox_global, pn.bbox_global)
            if not _node_match(tn, pn, iou, iou_threshold):
                continue
            if tn.label and _norm_tag(tn.label) == _norm_tag(pn.label):
                priority = 3
            elif _labels_share_root(tn.label, pn.label):
                priority = 2
            elif tn.kind == "opc" and pn.kind == "opc" and _opc_label_match(tn.label, pn.label):
                priority = 1
            else:
                priority = 0
            score = (priority, iou)
            if score > best_score:
                best_idx, best_score = j, score
        if best_idx >= 0:
            used.add(best_idx)
            tp += 1
    fp = len(p_filtered) - tp
    fn = len(t_filtered) - tp
    return _prf(tp, fp, fn)


def edge_f1(
    truth: ReconciledGraph,
    pred: ReconciledGraph,
    *,
    iou_threshold: float = 0.30,
) -> PRF:
    """Spec §9.1: edge match if both endpoints resolve to matched nodes
    AND line_type matches."""
    # First match nodes 1-1 (truth_id -> pred_id) using the same rule as
    # node_f1, but we need the mapping, not just counts.
    t_used: dict[str, str] = {}
    used_pred: set[str] = set()
    for tn in truth.nodes:
        best = None
        best_score = (-1, -1.0)
        for pn in pred.nodes:
            if pn.id in used_pred or pn.kind != tn.kind:
                continue
            iou = _bbox_iou(tn.bbox_global, pn.bbox_global)
            if not _node_match(tn, pn, iou, iou_threshold):
                continue
            if tn.label and _norm_tag(tn.label) == _norm_tag(pn.label):
                priority = 3
            elif _labels_share_root(tn.label, pn.label):
                priority = 2
            elif tn.kind == "opc" and pn.kind == "opc" and _opc_label_match(tn.label, pn.label):
                priority = 1
            else:
                priority = 0
            score = (priority, iou)
            if score > best_score:
                best = pn.id
                best_score = score
        if best is not None:
            t_used[tn.id] = best
            used_pred.add(best)

    def edge_key(e: ReconciledEdge, mapping: dict[str, str] | None = None) -> tuple:
        a, b = e.from_node, e.to_node
        if mapping:
            a = mapping.get(a, a)
            b = mapping.get(b, b)
        # Treat edges as undirected for matching.
        end = tuple(sorted((a, b)))
        return (end, e.line_type)

    truth_keys = {edge_key(e, t_used) for e in truth.edges}
    pred_keys = {edge_key(e) for e in pred.edges}
    tp = len(truth_keys & pred_keys)
    fp = len(pred_keys - truth_keys)
    fn = len(truth_keys - pred_keys)
    return _prf(tp, fp, fn)


def tag_ocr_exact_match(
    truth: list[ReconciledNode],
    pred: list[ReconciledNode],
    *,
    iou_threshold: float = 0.30,
) -> float:
    """Fraction of truth nodes whose matched prediction has identical
    normalised label. Truth nodes with no match score 0.

    The match rule is the same lenient ``_node_match`` used by ``node_f1``:
    same kind, and either spatial overlap (IoU ≥ threshold) or a label
    signal (equal normalised label, shared tag-root, or loose OPC token
    match). This makes the metric measure OCR fidelity *given the entity is
    identified*, rather than penalising correctly-OCR'd labels whose bbox
    happens to fall below the IoU threshold — which is the right framing
    when downstream consumers (control-logic derivation, tag look-up) key
    on the tag string, not the pixel coordinates.

    Within tie-eligible candidates, prefer the highest-IoU prediction so
    spatial agreement still acts as a tie-breaker; once paired, the score
    contribution is 1 iff the normalised labels agree exactly."""
    if not truth:
        return 1.0
    used: set[int] = set()
    matches = 0
    for tn in truth:
        best_idx = -1
        best_score: tuple[int, float] = (-1, -1.0)
        for j, pn in enumerate(pred):
            if j in used or pn.kind != tn.kind:
                continue
            iou = _bbox_iou(tn.bbox_global, pn.bbox_global)
            if not _node_match(tn, pn, iou, iou_threshold):
                continue
            label_eq = bool(tn.label) and _norm_tag(tn.label) == _norm_tag(pn.label)
            priority = 1 if label_eq else 0
            score = (priority, iou)
            if score > best_score:
                best_idx, best_score = j, score
        if best_idx >= 0:
            used.add(best_idx)
            if _norm_tag(tn.label) == _norm_tag(pred[best_idx].label):
                matches += 1
    return matches / len(truth)
