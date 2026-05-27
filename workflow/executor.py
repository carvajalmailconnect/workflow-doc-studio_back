"""
workflow/executor.py

Executes a workflow JSON graph and returns:
  - The templateJson from the document-designer node
  - The data context produced by traversing trigger → processors

Graph execution:
  1. Find the trigger node (webhook-trigger, schedule-trigger, etc.)
  2. Walk edges in topological order
  3. Each node type transforms the data context
  4. Return the document-designer node's templateJson + final data context

Node types handled:
  - webhook-trigger     → provides the incoming request data as context
  - data-processor      → applies field mappings/transformations (stub)
  - document-designer   → terminal; its templateJson is the render target
  - data-viewer         → pass-through (debug only, no transformation)
"""

from __future__ import annotations
from typing import Any


class WorkflowExecutionError(Exception):
    pass


def execute(workflow_json: dict, trigger_data: dict[str, Any]) -> tuple[dict, dict]:
    """
    Execute the workflow graph.

    Args:
        workflow_json: the full workflow JSON as saved by workflow-doc-studio.
        trigger_data:  the incoming data payload (e.g. webhook request body).

    Returns:
        (template_json, data_context)
        template_json — the templateJson from the document-designer node.
        data_context  — the resolved data dict to use for variable substitution.

    Raises:
        WorkflowExecutionError if no document-designer node is found.
    """
    nodes: dict[str, dict] = {n["id"]: n for n in workflow_json.get("nodes", [])}
    edges: list[dict] = workflow_json.get("edges", [])

    adjacency = _build_adjacency(edges)
    order = _topological_sort(nodes, adjacency)

    data_context: dict[str, Any] = dict(trigger_data)

    template_json: dict | None = None

    for node_id in order:
        node = nodes[node_id]
        node_type = node.get("type", "")
        config = node.get("data", {}).get("config", {})

        if node_type == "webhook-trigger":
            # Data is already seeded from trigger_data; validate schema if needed
            data_context = _apply_webhook_defaults(config, data_context)

        elif node_type == "data-processor":
            data_context = _apply_processor(config, data_context)

        elif node_type == "document-designer":
            template_json = config.get("templateJson")
            # document-designer is always terminal in the render pipeline

        elif node_type == "data-viewer":
            pass  # pass-through

        else:
            # Unknown node type — pass context through unchanged
            pass

    if template_json is None:
        raise WorkflowExecutionError(
            "Workflow has no document-designer node. Cannot generate PDF."
        )

    return template_json, data_context


# ── Node handlers ─────────────────────────────────────────────────────────────

def _apply_webhook_defaults(config: dict, data: dict) -> dict:
    """Inject default values for schema fields that are missing from trigger_data."""
    schema = config.get("schema", {})
    if not schema.get("enabled"):
        return data

    result = dict(data)
    for field_def in schema.get("fields", []):
        name = field_def.get("name", "")
        if name not in result and field_def.get("defaultValue") not in ("", None):
            result[name] = field_def["defaultValue"]

    return result


def _apply_processor(config: dict, data: dict) -> dict:
    """
    Apply field mappings defined in the data-processor node.

    Each field mapping has:
      { "source": "inputField", "target": "outputField", "transform": "..." }

    TODO: expand transforms (uppercase, number format, date format, etc.)
    as the data-processor UI is built out.
    """
    fields = config.get("fields", [])
    if not fields:
        return data

    result = dict(data)
    for mapping in fields:
        source = mapping.get("source", "")
        target = mapping.get("target", source)
        transform = mapping.get("transform", "none")

        value = _get_nested(data, source)
        if value is None:
            continue

        value = _apply_transform(value, transform)
        result[target] = value

    return result


def _apply_transform(value: Any, transform: str) -> Any:
    if transform == "uppercase" and isinstance(value, str):
        return value.upper()
    if transform == "lowercase" and isinstance(value, str):
        return value.lower()
    if transform == "capitalize" and isinstance(value, str):
        return value.title()
    if transform == "trim" and isinstance(value, str):
        return value.strip()
    return value


# ── Graph utilities ───────────────────────────────────────────────────────────

def _build_adjacency(edges: list[dict]) -> dict[str, list[str]]:
    """source_id → [target_id, ...]"""
    adj: dict[str, list[str]] = {}
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        adj.setdefault(src, []).append(tgt)
    return adj


def _topological_sort(
    nodes: dict[str, dict],
    adjacency: dict[str, list[str]],
) -> list[str]:
    """Kahn's algorithm — returns node IDs in execution order."""
    in_degree: dict[str, int] = {nid: 0 for nid in nodes}
    for targets in adjacency.values():
        for t in targets:
            if t in in_degree:
                in_degree[t] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order: list[str] = []

    while queue:
        node_id = queue.pop(0)
        order.append(node_id)
        for neighbour in adjacency.get(node_id, []):
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    return order


def _get_nested(data: Any, path: str) -> Any:
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current
