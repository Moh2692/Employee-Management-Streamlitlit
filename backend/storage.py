import json
import os
import threading
from pathlib import Path
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import uuid4


DATA_FILE = Path(__file__).resolve().parents[1] / "resources" / "employees.json"
_file_lock = threading.Lock()
Result = TypeVar("Result")


def _read_employees() -> list[dict[str, Any]]:
    try:
        with DATA_FILE.open(encoding="utf-8") as file:
            employees = json.load(file)
    except FileNotFoundError:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        employees = []
        _write_employees(employees)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Employee database contains invalid JSON: {error}") from error

    if not isinstance(employees, list):
        raise RuntimeError("Employee database must contain a JSON list.")
    return employees


def read_employees() -> list[dict[str, Any]]:
    with _file_lock:
        return _read_employees()


def mutate_employees(
    mutation: Callable[[list[dict[str, Any]]], tuple[Result, bool]],
) -> Result:
    with _file_lock:
        employees = _read_employees()
        result, changed = mutation(employees)
        if changed:
            _write_employees(employees)
        return result


def write_employees(employees: list[dict[str, Any]]) -> None:
    with _file_lock:
        _write_employees(employees)


def _write_employees(employees: list[dict[str, Any]]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_name(f".{DATA_FILE.name}.{uuid4().hex}.tmp")
    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(employees, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temporary_file, DATA_FILE)
    finally:
        temporary_file.unlink(missing_ok=True)
