"""Persistent review sessions for the local P&ID review workbench.

The extractor's graph is immutable.  A review session is reconstructed by
replaying append-only events against that graph; ``state.json`` is only a
cache for humans and recovery tooling.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from diagex.dexpi_schema import (
    EQUIPMENT_CLASS_KEYS,
    INSTRUMENT_CLASS_KEYS,
    INSTRUMENT_FUNCTION_KEYS,
    VALVE_TYPE_KEYS,
)
from diagex.vision.models import ReconciledEdge, ReconciledGraph, ReconciledNode

SCHEMA_VERSION = "1.0.0"
REVIEW_STATES = {"unreviewed", "approved", "modified", "rejected", "waived", "resolved"}
PAGE_ROLES = {"pid", "legend", "cover", "notes", "other"}
LINE_TYPES = {
    "process",
    "signal_electric",
    "signal_pneumatic",
    "instrument_capillary",
    "electrical_power",
    "other",
}
KINDS = {"equipment", "instrument", "line", "connection", "text", "note", "opc"}


class ReviewError(RuntimeError):
    """Base class for review-session failures."""


class ReviewConflictError(ReviewError):
    """Raised when a stale browser revision or mismatched source is supplied."""


class ReviewIncompleteError(ReviewError):
    """Raised when export is requested before the review is complete."""

    def __init__(self, message: str, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details


class ReviewValidationError(ReviewError):
    """Raised when a reviewed graph cannot produce a valid DEXPI model."""

    def __init__(self, message: str, report: dict[str, Any]) -> None:
        super().__init__(message)
        self.report = report


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any, length: int = 12) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def resolve_graph_path(target: Path | str) -> Path:
    path = Path(target).expanduser().resolve()
    if path.is_dir():
        path = path / "graph.json"
    if not path.is_file():
        raise FileNotFoundError(f"review graph not found: {path}")
    return path


def _load_build_issues(graph_path: Path) -> list[dict[str, Any]]:
    result_path = graph_path.with_name("result.json")
    if not result_path.exists():
        return []
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: list[dict[str, Any]] = []
    for index, message in enumerate(result.get("dexpi_issues") or []):
        text = str(message)
        match = re.search(r"\b(?:node|edge) '([^']+)'", text)
        out.append(
            {
                "id": f"b-{index:04d}-{_canonical_hash(text, 8)}",
                "message": text,
                "target_id": match.group(1) if match else None,
            }
        )
    return out


def _load_page_manifest(graph_path: Path) -> dict[str, Any] | None:
    path = graph_path.with_name("pages.json")
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) and isinstance(value.get("pages"), list) else None


def _conflict_records(graph: ReconciledGraph) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, conflict in enumerate(graph.conflicts):
        records.append(
            {
                "id": f"c-{index:04d}-{_canonical_hash(conflict, 8)}",
                "conflict": copy.deepcopy(conflict),
            }
        )
    return records


def _initial_state(graph: ReconciledGraph, session: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "base_graph_sha256": session["graph_sha256"],
        "graph": graph.model_dump(mode="json"),
        "page_reviews": {
            str(page["page_index"]): {
                "status": "unreviewed",
                "role": None,
                "reason": None,
            }
            for page in session["pages"]
        },
        "node_reviews": {node.id: "unreviewed" for node in graph.nodes},
        "edge_reviews": {edge.id: "unreviewed" for edge in graph.edges},
        "conflict_reviews": {
            item["id"]: {
                "status": "unreviewed",
                "reason": None,
                "conflict": item["conflict"],
            }
            for item in session["conflicts"]
        },
        "warnings": [],
        "updated_at": session["created_at"],
    }


def _find_object(items: list[dict[str, Any]], object_id: str) -> dict[str, Any] | None:
    return next((item for item in items if item.get("id") == object_id), None)


def _replace_object(items: list[dict[str, Any]], object_id: str, value: dict[str, Any] | None) -> None:
    position = next((i for i, item in enumerate(items) if item.get("id") == object_id), None)
    if value is None:
        if position is not None:
            items.pop(position)
        return
    if position is None:
        items.append(copy.deepcopy(value))
    else:
        items[position] = copy.deepcopy(value)


def _target_snapshot(state: dict[str, Any], target_type: str, target_id: str) -> Any:
    if target_type == "node":
        return {
            "object": copy.deepcopy(_find_object(state["graph"]["nodes"], target_id)),
            "status": state["node_reviews"].get(target_id),
        }
    if target_type == "edge":
        return {
            "object": copy.deepcopy(_find_object(state["graph"]["edges"], target_id)),
            "status": state["edge_reviews"].get(target_id),
        }
    if target_type == "page":
        return copy.deepcopy(state["page_reviews"].get(target_id))
    if target_type == "conflict":
        return copy.deepcopy(state["conflict_reviews"].get(target_id))
    raise ValueError(f"unknown review target type: {target_type}")


def _apply_snapshot(state: dict[str, Any], target_type: str, target_id: str, value: Any) -> None:
    if target_type == "node":
        _replace_object(state["graph"]["nodes"], target_id, value.get("object") if value else None)
        if value is None or value.get("status") is None:
            state["node_reviews"].pop(target_id, None)
        else:
            state["node_reviews"][target_id] = value["status"]
        return
    if target_type == "edge":
        _replace_object(state["graph"]["edges"], target_id, value.get("object") if value else None)
        if value is None or value.get("status") is None:
            state["edge_reviews"].pop(target_id, None)
        else:
            state["edge_reviews"][target_id] = value["status"]
        return
    if target_type == "page":
        if value is None:
            state["page_reviews"].pop(target_id, None)
        else:
            state["page_reviews"][target_id] = copy.deepcopy(value)
        return
    if target_type == "conflict":
        if value is None:
            state["conflict_reviews"].pop(target_id, None)
        else:
            state["conflict_reviews"][target_id] = copy.deepcopy(value)
        return
    raise ValueError(f"unknown review target type: {target_type}")


def _apply_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    _apply_snapshot(state, event["target_type"], event["target_id"], event.get("after"))
    state["revision"] = int(event["revision"])
    state["updated_at"] = event["timestamp"]


def _read_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            warnings.append(f"ignored malformed events.jsonl line {line_number}")
    return events, warnings


class ReviewStore:
    """Thread-safe, event-sourced review session."""

    def __init__(
        self,
        *,
        graph_path: Path,
        source_path: Path,
        out_dir: Path,
        rater: str,
    ) -> None:
        from diagex.review.render import prepare_page_assets

        self.graph_path = resolve_graph_path(graph_path)
        self.source_path = Path(source_path).expanduser().resolve()
        if not self.source_path.is_file():
            raise FileNotFoundError(f"source diagram not found: {self.source_path}")
        if not rater.strip():
            raise ValueError("--rater must not be empty")
        self.out_dir = Path(out_dir).expanduser().resolve()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = self.out_dir / "session.json"
        self.events_path = self.out_dir / "events.jsonl"
        self.state_path = self.out_dir / "state.json"
        self._lock = threading.RLock()

        graph = ReconciledGraph.model_validate_json(self.graph_path.read_text(encoding="utf-8"))
        graph_sha = _file_sha256(self.graph_path)
        source_sha = _file_sha256(self.source_path)
        if self.session_path.exists():
            session = json.loads(self.session_path.read_text(encoding="utf-8"))
            if session.get("graph_sha256") != graph_sha:
                raise ReviewConflictError(
                    "the source graph changed after this review session was created; "
                    "choose another --out-dir to start a new review"
                )
            if session.get("source_sha256") != source_sha:
                raise ReviewConflictError(
                    "the source diagram changed after this review session was created; "
                    "choose another --out-dir to start a new review"
                )
            if session.get("rater") != rater:
                raise ReviewConflictError(
                    f"this single-reviewer session belongs to {session.get('rater')!r}, not {rater!r}"
                )
            pages = prepare_page_assets(self.source_path, self.out_dir / "pages", cached=session.get("pages"))
            session["pages"] = pages
        else:
            pages = prepare_page_assets(
                self.source_path,
                self.out_dir / "pages",
                expected=_load_page_manifest(self.graph_path),
            )
            session = {
                "schema_version": SCHEMA_VERSION,
                "created_at": _utc_now(),
                "rater": rater,
                "graph_path": str(self.graph_path),
                "source_path": str(self.source_path),
                "graph_sha256": graph_sha,
                "source_sha256": source_sha,
                "pages": pages,
                "conflicts": _conflict_records(graph),
                "build_issues": _load_build_issues(self.graph_path),
            }
        self.session = session
        _atomic_json(self.session_path, self.session)

        self.base_graph = graph
        self.events, event_warnings = _read_events(self.events_path)
        self.state = _initial_state(graph, self.session)
        for event in self.events:
            if event.get("base_graph_sha256") != graph_sha:
                raise ReviewConflictError("an event belongs to a different source graph")
            _apply_event(self.state, event)
        self.state["warnings"] = event_warnings + self._geometry_warnings()
        _atomic_json(self.state_path, self.state)

    @classmethod
    def open(
        cls,
        target: Path | str,
        *,
        source_path: Path | str,
        rater: str,
        out_dir: Path | str | None = None,
    ) -> ReviewStore:
        graph_path = resolve_graph_path(target)
        review_dir = Path(out_dir) if out_dir is not None else graph_path.parent / "review"
        return cls(
            graph_path=graph_path,
            source_path=Path(source_path),
            out_dir=review_dir,
            rater=rater,
        )

    def _geometry_warnings(self) -> list[str]:
        page_dims = {
            int(page["page_index"]): (int(page["width"]), int(page["height"]))
            for page in self.session["pages"]
        }
        warnings: list[str] = []
        for node in self.base_graph.nodes:
            dims = page_dims.get(node.page_index)
            if dims is None:
                warnings.append(f"node {node.id} references missing page {node.page_index + 1}")
                continue
            box = node.bbox_global
            if box.x < 0 or box.y < 0 or box.x2 > dims[0] or box.y2 > dims[1]:
                warnings.append(f"node {node.id} falls outside rendered page {node.page_index + 1}")
        return warnings

    def _append_event_record(self, event: dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        needs_separator = self.events_path.exists() and self.events_path.stat().st_size > 0
        if needs_separator:
            with self.events_path.open("rb") as check:
                check.seek(-1, os.SEEK_END)
                needs_separator = check.read(1) != b"\n"
        with self.events_path.open("a", encoding="utf-8") as handle:
            if needs_separator:
                handle.write("\n")
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _normal_after(
        self,
        target_type: str,
        target_id: str,
        operation: str,
        payload: dict[str, Any],
        reason: str | None,
    ) -> Any:
        before = _target_snapshot(self.state, target_type, target_id)
        if target_type == "page":
            if before is None:
                raise KeyError(f"unknown page {target_id}")
            role = str(payload.get("role") or before.get("role") or "")
            if role not in PAGE_ROLES:
                raise ValueError(f"page role must be one of {sorted(PAGE_ROLES)}")
            if operation not in {"approve", "waive", "modify"}:
                raise ValueError("pages support approve, modify, or waive")
            return {
                "status": "waived" if operation == "waive" else "approved",
                "role": role,
                "reason": reason,
            }
        if target_type == "conflict":
            if before is None:
                raise KeyError(f"unknown conflict {target_id}")
            if operation not in {"resolve", "waive"}:
                raise ValueError("conflicts support resolve or waive")
            after = copy.deepcopy(before)
            after["status"] = "resolved" if operation == "resolve" else "waived"
            after["reason"] = reason
            return after
        if target_type not in {"node", "edge"}:
            raise ValueError(f"unknown target type: {target_type}")
        model_cls = ReconciledNode if target_type == "node" else ReconciledEdge
        if operation == "add":
            if before and before.get("object") is not None:
                raise ValueError(f"{target_type} {target_id} already exists")
            candidate = {**payload, "id": target_id}
            obj = model_cls.model_validate(candidate).model_dump(mode="json")
            return {"object": obj, "status": "modified"}
        if before is None or before.get("object") is None:
            raise KeyError(f"unknown {target_type} {target_id}")
        if operation == "approve":
            return {"object": copy.deepcopy(before["object"]), "status": "approved"}
        if operation == "reject":
            return {"object": copy.deepcopy(before["object"]), "status": "rejected"}
        if operation == "modify":
            candidate = copy.deepcopy(before["object"])
            candidate.update(payload)
            candidate["id"] = target_id
            obj = model_cls.model_validate(candidate).model_dump(mode="json")
            return {"object": obj, "status": "modified"}
        raise ValueError(f"unsupported {target_type} operation: {operation}")

    def append_action(self, request: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            expected = int(request.get("expected_revision", -1))
            if expected != int(self.state["revision"]):
                raise ReviewConflictError(
                    f"stale review revision {expected}; current revision is {self.state['revision']}"
                )
            operation = str(request.get("operation") or "")
            if operation == "undo":
                return self._undo(request)
            target_type = str(request.get("target_type") or "")
            target_id = str(request.get("target_id") or "")
            if operation == "add" and not target_id:
                prefix = "n" if target_type == "node" else "e"
                target_id = f"{prefix}-{uuid.uuid4().hex[:8]}"
            if not target_id:
                raise ValueError("target_id is required")
            payload = request.get("after") or {}
            if not isinstance(payload, dict):
                raise ValueError("after must be an object")
            reason = str(request.get("reason") or "").strip() or None
            before = _target_snapshot(self.state, target_type, target_id)
            after = self._normal_after(target_type, target_id, operation, payload, reason)
            event = {
                "schema_version": SCHEMA_VERSION,
                "revision": int(self.state["revision"]) + 1,
                "timestamp": _utc_now(),
                "reviewer": self.session["rater"],
                "base_graph_sha256": self.session["graph_sha256"],
                "target_type": target_type,
                "target_id": target_id,
                "operation": operation,
                "before": before,
                "after": after,
                "reason": reason,
            }
            self._commit_event(event)
            return {"event": event, "state": self.public_state()}

    def _undo(self, request: dict[str, Any]) -> dict[str, Any]:
        undone = {int(event["undo_of"]) for event in self.events if event.get("undo_of") is not None}
        candidate = next(
            (
                event for event in reversed(self.events)
                if event.get("operation") != "undo" and int(event["revision"]) not in undone
            ),
            None,
        )
        if candidate is None:
            raise ValueError("nothing to undo")
        target_type = candidate["target_type"]
        target_id = candidate["target_id"]
        event = {
            "schema_version": SCHEMA_VERSION,
            "revision": int(self.state["revision"]) + 1,
            "timestamp": _utc_now(),
            "reviewer": self.session["rater"],
            "base_graph_sha256": self.session["graph_sha256"],
            "target_type": target_type,
            "target_id": target_id,
            "operation": "undo",
            "undo_of": candidate["revision"],
            "before": _target_snapshot(self.state, target_type, target_id),
            "after": copy.deepcopy(candidate.get("before")),
            "reason": str(request.get("reason") or "").strip() or None,
        }
        self._commit_event(event)
        return {"event": event, "state": self.public_state()}

    def _commit_event(self, event: dict[str, Any]) -> None:
        self._append_event_record(event)
        self.events.append(event)
        _apply_event(self.state, event)
        _atomic_json(self.state_path, self.state)

    def reviewed_graph(self) -> ReconciledGraph:
        raw = copy.deepcopy(self.state["graph"])
        active_nodes = {
            node["id"]
            for node in raw["nodes"]
            if self.state["node_reviews"].get(node["id"]) != "rejected"
        }
        raw["nodes"] = [node for node in raw["nodes"] if node["id"] in active_nodes]
        raw["edges"] = [
            edge for edge in raw["edges"]
            if self.state["edge_reviews"].get(edge["id"]) != "rejected"
        ]
        raw["conflicts"] = [
            {
                **copy.deepcopy(item["conflict"]),
                "review_status": item["status"],
                "review_reason": item.get("reason"),
            }
            for item in self.state["conflict_reviews"].values()
        ]
        return ReconciledGraph.model_validate(raw)

    def completion(self) -> dict[str, Any]:
        unreviewed_pages = [
            page_id for page_id, review in self.state["page_reviews"].items()
            if review.get("status") not in {"approved", "waived"} or review.get("role") not in PAGE_ROLES
        ]
        unreviewed_nodes = [
            object_id for object_id, status in self.state["node_reviews"].items()
            if status == "unreviewed"
        ]
        unreviewed_edges = [
            object_id for object_id, status in self.state["edge_reviews"].items()
            if status == "unreviewed"
        ]
        unresolved_conflicts = [
            conflict_id for conflict_id, review in self.state["conflict_reviews"].items()
            if review.get("status") not in {"resolved", "waived"}
        ]
        graph = self.reviewed_graph()
        node_ids = {node.id for node in graph.nodes}
        dangling_edges = [
            edge.id for edge in graph.edges
            if edge.from_node not in node_ids or edge.to_node not in node_ids
        ]
        details = {
            "unreviewed_pages": unreviewed_pages,
            "unreviewed_nodes": unreviewed_nodes,
            "unreviewed_edges": unreviewed_edges,
            "unresolved_conflicts": unresolved_conflicts,
            "dangling_edges": dangling_edges,
        }
        details["complete"] = not any(details[key] for key in details if key != "complete")
        return details

    def _queue(self) -> list[dict[str, Any]]:
        graph = self.state["graph"]
        conflict_text = json.dumps(self.session.get("conflicts") or [], ensure_ascii=False)
        issue_targets = {
            item.get("target_id") for item in self.session.get("build_issues") or [] if item.get("target_id")
        }
        partial_pages = {
            int(page) for page, status in (graph.get("per_page_status") or {}).items()
            if status in {"partial", "error", "cost_exhausted"}
        }
        node_by_id = {node["id"]: node for node in graph["nodes"]}
        rows: list[dict[str, Any]] = []
        for node in graph["nodes"]:
            reasons: list[str] = []
            if node["page_index"] in partial_pages:
                reasons.append("partial page")
            if node["id"] in conflict_text:
                reasons.append("graph conflict")
            if node["id"] in issue_targets:
                reasons.append("build issue")
            if node.get("confidence") in {"medium", "low"}:
                reasons.append(f"{node['confidence']} confidence")
            attrs = node.get("attributes") or {}
            if node.get("kind") == "equipment" and not attrs.get("equipment_class"):
                reasons.append("unclassified")
            tier = 0 if any(reason in {"partial page", "graph conflict"} for reason in reasons) else (1 if reasons else 2)
            box = node["bbox_global"]
            rows.append(
                {
                    "target_type": "node",
                    "target_id": node["id"],
                    "page_index": node["page_index"],
                    "label": node.get("label") or node["id"],
                    "status": self.state["node_reviews"].get(node["id"], "unreviewed"),
                    "tier": tier,
                    "reasons": reasons,
                    "sort": [tier, node["page_index"], box["y"], box["x"], node["id"]],
                }
            )
        for edge in graph["edges"]:
            start = node_by_id.get(edge["from_node"], {})
            page_index = int(start.get("page_index", 0))
            reasons = []
            if page_index in partial_pages:
                reasons.append("partial page")
            if edge["id"] in conflict_text:
                reasons.append("graph conflict")
            if edge["id"] in issue_targets:
                reasons.append("build issue")
            if edge.get("confidence") in {"medium", "low"}:
                reasons.append(f"{edge['confidence']} confidence")
            if edge["from_node"] not in node_by_id or edge["to_node"] not in node_by_id:
                reasons.append("dangling endpoint")
            tier = 0 if any(reason in {"partial page", "graph conflict"} for reason in reasons) else (1 if reasons else 2)
            label = (edge.get("attributes") or {}).get("line_id") or f"{edge['from_node']} → {edge['to_node']}"
            rows.append(
                {
                    "target_type": "edge",
                    "target_id": edge["id"],
                    "page_index": page_index,
                    "label": label,
                    "status": self.state["edge_reviews"].get(edge["id"], "unreviewed"),
                    "tier": tier,
                    "reasons": reasons,
                    "sort": [tier, page_index, 0, 0, edge["id"]],
                }
            )
        rows.sort(key=lambda row: row.pop("sort"))
        return rows

    def public_state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "session": self.session,
                "revision": self.state["revision"],
                "graph": self.state["graph"],
                "reviews": {
                    "pages": self.state["page_reviews"],
                    "nodes": self.state["node_reviews"],
                    "edges": self.state["edge_reviews"],
                    "conflicts": self.state["conflict_reviews"],
                },
                "warnings": self.state.get("warnings") or [],
                "completion": self.completion(),
                "queue": self._queue(),
                "taxonomy": {
                    "kinds": sorted(KINDS),
                    "line_types": sorted(LINE_TYPES),
                    "page_roles": sorted(PAGE_ROLES),
                    "equipment_classes": list(EQUIPMENT_CLASS_KEYS),
                    "valve_types": list(VALVE_TYPE_KEYS),
                    "instrument_functions": list(INSTRUMENT_FUNCTION_KEYS),
                    "instrument_classes": list(INSTRUMENT_CLASS_KEYS),
                },
            }

    def finish(self) -> dict[str, Any]:
        with self._lock:
            completion = self.completion()
            if not completion["complete"]:
                raise ReviewIncompleteError("review coverage is incomplete", completion)

            from diagex.dexpi import validate as dexpi_validate
            from diagex.dexpi import xml_io
            from diagex.extractors.dexpi_builder import build_dexpi, serialize_model, validate_model

            graph = self.reviewed_graph()
            build = build_dexpi(graph)
            roundtrip_errors = validate_model(build.model)
            semantic = dexpi_validate.semantic_validate(build.model)
            semantic_rows = [asdict(issue) for issue in semantic]
            errors = [*roundtrip_errors, *[row for row in semantic_rows if row["severity"] == "error"]]
            report: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "finished": False,
                "finished_at": _utc_now(),
                "reviewer": self.session["rater"],
                "base_graph_sha256": self.session["graph_sha256"],
                "revision": self.state["revision"],
                "coverage": completion,
                "review_counts": {
                    "pages": _status_counts(self.state["page_reviews"], nested=True),
                    "nodes": _status_counts(self.state["node_reviews"]),
                    "edges": _status_counts(self.state["edge_reviews"]),
                    "conflicts": _status_counts(self.state["conflict_reviews"], nested=True),
                },
                "graph_counts": {"nodes": len(graph.nodes), "edges": len(graph.edges)},
                "dexpi_stats": build.stats,
                "build_issues": build.issues,
                "roundtrip_errors": roundtrip_errors,
                "semantic_issues": semantic_rows,
                "xsd": {"status": "pending", "issues": []},
                "outputs": {},
            }
            if errors:
                _atomic_json(self.out_dir / "review.report.json", report)
                raise ReviewValidationError("reviewed graph failed DEXPI validation", report)

            temp_dir = self.out_dir / ".export-tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            tmp_json = serialize_model(build.model, temp_dir, "pid.reviewed.dexpi")
            tmp_xml = temp_dir / "pid.reviewed.dexpi.xml"
            xml_io.dump(build.model, tmp_xml)
            try:
                xsd_issues = dexpi_validate.xsd_validate(tmp_xml)
                report["xsd"] = {"status": "ran", "issues": [asdict(issue) for issue in xsd_issues]}
            except dexpi_validate.XmlschemaUnavailableError as exc:
                report["xsd"] = {"status": "skipped", "message": str(exc), "issues": []}
                xsd_issues = []
            if dexpi_validate.has_errors(xsd_issues):
                _atomic_json(self.out_dir / "review.report.json", report)
                raise ReviewValidationError("reviewed XML failed XSD validation", report)

            graph_target = self.out_dir / "graph.reviewed.json"
            json_target = self.out_dir / "pid.reviewed.dexpi.json"
            xml_target = self.out_dir / "pid.reviewed.dexpi.xml"
            _atomic_json(graph_target, graph.model_dump(mode="json"))
            os.replace(tmp_json, json_target)
            os.replace(tmp_xml, xml_target)
            try:
                temp_dir.rmdir()
            except OSError:
                pass
            report["finished"] = True
            report["outputs"] = {
                "graph": str(graph_target),
                "dexpi_json": str(json_target),
                "dexpi_xml": str(xml_target),
            }
            _atomic_json(self.out_dir / "review.report.json", report)
            return report


def _status_counts(values: dict[str, Any], *, nested: bool = False) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values.values():
        status = str(value.get("status")) if nested else str(value)
        counts[status] = counts.get(status, 0) + 1
    return counts
