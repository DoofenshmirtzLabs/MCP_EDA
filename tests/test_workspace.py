from eda_mcp.services.workspace import validate_name

def test_valid_project_name():
    assert validate_name("counter_4bit") == "counter_4bit"

def test_reject_path_traversal():
    try:
        validate_name("../outside")
    except ValueError:
        return
    raise AssertionError("Path traversal name was accepted")
