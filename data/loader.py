import json
from pathlib import Path
from typing import Any


def load_budgets() -> list[dict[str, Any]]:
    """Load budget records from mock_data/budgets.json."""
    project_root = Path(__file__).resolve().parents[1]
    file_path = project_root / "mock_data" / "budgets.json"
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def load_vendors() -> list[dict[str, Any]]:
    """Load vendor records from mock_data/vendors.json."""
    project_root = Path(__file__).resolve().parents[1]
    file_path = project_root / "mock_data" / "vendors.json"
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def load_policies() -> list[dict[str, Any]]:
    """Load policy records from mock_data/policies.json."""
    project_root = Path(__file__).resolve().parents[1]
    file_path = project_root / "mock_data" / "policies.json"
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def load_requests() -> list[dict[str, Any]]:
    """Load purchase request records from mock_data/requests.json."""
    project_root = Path(__file__).resolve().parents[1]
    file_path = project_root / "mock_data" / "requests.json"
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data
