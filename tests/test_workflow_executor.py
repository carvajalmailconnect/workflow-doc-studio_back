import pytest
from workflow.executor import execute, WorkflowExecutionError


def test_execute_single_designer(minimal_template):
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "designer-1",
                "type": "document-designer",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {"templateJson": minimal_template},
                    "locked": False,
                    "definitionType": "document-designer",
                },
            }
        ],
        "edges": [],
    }
    template, data = execute(workflow, {"name": "Oscar"})
    assert template is minimal_template
    assert data["name"] == "Oscar"


def test_execute_webhook_injects_defaults(minimal_template):
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "wh-1",
                "type": "webhook-trigger",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {
                        "schema": {
                            "enabled": True,
                            "fields": [
                                {"id": "f1", "name": "source", "type": "string",
                                 "required": False, "defaultValue": "web",
                                 "enum": [], "children": []},
                            ],
                        }
                    },
                    "locked": False,
                    "definitionType": "webhook-trigger",
                },
            },
            {
                "id": "designer-1",
                "type": "document-designer",
                "position": {"x": 200, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {"templateJson": minimal_template},
                    "locked": False,
                    "definitionType": "document-designer",
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "wh-1", "target": "designer-1",
             "sourceHandle": "out", "targetHandle": "in"}
        ],
    }
    template, data = execute(workflow, {"userId": 1})
    assert data["source"] == "web"
    assert data["userId"] == 1


def test_execute_raises_without_designer():
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "wh-1",
                "type": "webhook-trigger",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {"config": {}, "locked": False, "definitionType": "webhook-trigger"},
            }
        ],
        "edges": [],
    }
    with pytest.raises(WorkflowExecutionError):
        execute(workflow, {})


def test_topological_order(minimal_template):
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "designer-1",
                "type": "document-designer",
                "position": {"x": 400, "y": 0},
                "zIndex": 1,
                "data": {"config": {"templateJson": minimal_template},
                         "locked": False, "definitionType": "document-designer"},
            },
            {
                "id": "processor-1",
                "type": "data-processor",
                "position": {"x": 200, "y": 0},
                "zIndex": 1,
                "data": {"config": {"fields": [], "stopOnError": False},
                         "locked": False, "definitionType": "data-processor"},
            },
            {
                "id": "wh-1",
                "type": "webhook-trigger",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {"config": {"schema": {"enabled": False, "fields": []}},
                         "locked": False, "definitionType": "webhook-trigger"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "wh-1",       "target": "processor-1", "sourceHandle": "out", "targetHandle": "in"},
            {"id": "e2", "source": "processor-1", "target": "designer-1",  "sourceHandle": "out", "targetHandle": "in"},
        ],
    }
    template, data = execute(workflow, {"userId": 99})
    assert template is minimal_template
    assert data["userId"] == 99


def test_processor_transform_uppercase(minimal_template):
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "proc-1",
                "type": "data-processor",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {
                        "fields": [
                            {"source": "name", "target": "nameUpper", "transform": "uppercase"}
                        ],
                        "stopOnError": False,
                    },
                    "locked": False, "definitionType": "data-processor",
                },
            },
            {
                "id": "designer-1",
                "type": "document-designer",
                "position": {"x": 200, "y": 0},
                "zIndex": 1,
                "data": {"config": {"templateJson": minimal_template},
                         "locked": False, "definitionType": "document-designer"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "proc-1", "target": "designer-1",
             "sourceHandle": "out", "targetHandle": "in"}
        ],
    }
    _, data = execute(workflow, {"name": "oscar"})
    assert data["nameUpper"] == "OSCAR"
