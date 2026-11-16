import re
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.storage import mutate_employees, read_employees


class EmployeeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=120)
    department: str = Field(min_length=1, max_length=120)
    position: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=40)
    status: Literal["Active", "On leave", "Inactive"] = "Active"

    @field_validator("name", "department", "position", "phone", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("name", "department", "position")
    @classmethod
    def require_non_whitespace(cls, value: str) -> str:
        if not value:
            raise ValueError("This field must not be blank.")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("A valid email address is required.")
        return value


class Employee(EmployeeInput):
    id: str
    createdAt: str
    updatedAt: str | None = None


app = FastAPI(title="Employee Management API", version="1.0.0")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "employee-management-api"}


@app.get("/api/employees", response_model=list[Employee], tags=["employees"])
def list_employees() -> list[dict]:
    return read_employees()


@app.get("/api/employees/{employee_id}", response_model=Employee, tags=["employees"])
def get_employee(employee_id: str) -> dict:
    employee = next(
        (record for record in read_employees() if record["id"] == employee_id),
        None,
    )
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return employee


@app.post(
    "/api/employees",
    response_model=Employee,
    status_code=status.HTTP_201_CREATED,
    tags=["employees"],
)
def create_employee(employee: EmployeeInput) -> dict:
    def create(records: list[dict]) -> tuple[dict, bool]:
        if any(record["email"].lower() == employee.email for record in records):
            raise HTTPException(
                status_code=409,
                detail="An employee with this email already exists.",
            )

        created = Employee(
            id=str(uuid4()),
            createdAt=datetime.now(timezone.utc).isoformat(),
            **employee.model_dump(),
        ).model_dump()
        records.append(created)
        return created, True

    return mutate_employees(create)


@app.put("/api/employees/{employee_id}", response_model=Employee, tags=["employees"])
def update_employee(employee_id: str, employee: EmployeeInput) -> dict:
    def update(records: list[dict]) -> tuple[dict, bool]:
        index = next(
            (i for i, record in enumerate(records) if record["id"] == employee_id),
            None,
        )
        if index is None:
            raise HTTPException(status_code=404, detail="Employee not found.")
        if any(
            record["email"].lower() == employee.email and i != index
            for i, record in enumerate(records)
        ):
            raise HTTPException(
                status_code=409,
                detail="An employee with this email already exists.",
            )

        updated = {
            **records[index],
            **employee.model_dump(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        records[index] = updated
        return updated, True

    return mutate_employees(update)


@app.delete(
    "/api/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["employees"],
)
def delete_employee(employee_id: str) -> Response:
    def delete(records: list[dict]) -> tuple[None, bool]:
        remaining = [record for record in records if record["id"] != employee_id]
        if len(remaining) == len(records):
            raise HTTPException(status_code=404, detail="Employee not found.")
        records[:] = remaining
        return None, True

    mutate_employees(delete)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
