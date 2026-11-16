import csv
import io
import os
from datetime import date

import requests
import streamlit as st


API_URL = os.getenv("EMPLOYEE_API_URL", "http://127.0.0.1:8000").rstrip("/")
STATUSES = ["Active", "On leave", "Inactive"]

st.set_page_config(
    page_title="People | Northstar",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    .stApp { background: #f7f8fa; font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.035em; }
    .block-container { max-width: 1440px; padding-top: 2rem; }
    [data-testid="stMetric"] { background: white; border: 1px solid #edecf1; border-radius: 12px; padding: 18px 20px; }
    [data-testid="stMetricLabel"] { color: #777985; }
    [data-testid="stMetricValue"] { color: #24232b; }
    div.stButton > button[kind="primary"] { background: #7658dc; border-color: #7658dc; }
    div.stButton > button[kind="primary"]:hover { background: #6546d2; border-color: #6546d2; }
    .employee-card { background: white; border: 1px solid #edecf1; border-radius: 10px; padding: 12px 16px; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method: str, path: str, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            timeout=8,
            **kwargs,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not reach the FastAPI backend at {API_URL}. "
            "Start it with `uvicorn backend.main:app --reload`."
        ) from error

    if not response.ok:
        try:
            message = response.json().get("detail", response.text)
        except requests.exceptions.JSONDecodeError:
            message = response.text
        if isinstance(message, list):
            message = "; ".join(item.get("msg", str(item)) for item in message)
        raise RuntimeError(str(message))

    return response.json() if response.content else None


def get_employees() -> list[dict]:
    return api_request("GET", "/api/employees")


def initials(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


def employee_csv(records: list[dict]) -> bytes:
    output = io.StringIO(newline="")
    columns = ["name", "email", "department", "position", "status", "phone"]
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for record in records:
        writer.writerow({key: record.get(key, "") for key in columns})
    return output.getvalue().encode("utf-8")


try:
    health = api_request("GET", "/api/health")
    employees = get_employees()
except RuntimeError as error:
    st.title("Northstar")
    st.error(str(error))
    st.stop()

with st.sidebar:
    st.markdown("## ✳ northstar.")
    st.caption("YOUR WORKSPACE")
    st.markdown("**▣  Northstar Studio**")
    st.divider()
    st.markdown("### ♙  People")
    st.caption("Your team, all in one place.")
    st.divider()
    st.markdown("**Jordan Davis**  ·  Admin")
    st.caption(f"API status: {health['status']}")

st.caption(f"WORKSPACE  /  PEOPLE                                      {date.today():%a, %b %d}")
heading, add_column = st.columns([5, 1])
with heading:
    st.title("People ✳")
    st.caption("A little bit of everyone who makes it happen.")
with add_column:
    st.write("")
    st.write("")
    add_clicked = st.button("＋ Add employee", type="primary", use_container_width=True)

active_count = sum(employee["status"] == "Active" for employee in employees)
department_count = len({employee["department"] for employee in employees})
metric_columns = st.columns(3)
metric_columns[0].metric("Total employees", len(employees), help="Everyone in your directory")
metric_columns[1].metric("Active today", active_count, help="Employees with active status")
metric_columns[2].metric("Departments", department_count, help="Teams represented in your directory")

st.write("")
directory_heading, export_column = st.columns([5, 1])
with directory_heading:
    st.subheader(f"The directory  ·  {len(employees)}")
    st.caption("Get to know the people behind the work.")
with export_column:
    st.download_button(
        "↓ Export CSV",
        data=employee_csv(employees),
        file_name="employees.csv",
        mime="text/csv",
        use_container_width=True,
    )

search_column, department_column, status_column = st.columns([3, 2, 1.5])
search = search_column.text_input("Search people", placeholder="Name, email, title...")
departments = sorted({employee["department"] for employee in employees})
department = department_column.selectbox("Department", ["All departments", *departments])
status = status_column.selectbox("Status", ["All statuses", *STATUSES])

filtered_employees = [
    employee for employee in employees
    if search.casefold() in " ".join(
        str(employee.get(field, ""))
        for field in ("name", "email", "position", "department")
    ).casefold()
    and (department == "All departments" or employee["department"] == department)
    and (status == "All statuses" or employee["status"] == status)
]

st.markdown("---")
if not filtered_employees:
    st.info("No employees match those filters. Try another search or add a teammate.")
else:
    for employee in filtered_employees:
        with st.container(border=True):
            employee_column, department_column, status_column, phone_column, actions_column = st.columns(
                [3, 1.7, 1.2, 1.6, 1.2],
                vertical_alignment="center",
            )
            with employee_column:
                st.markdown(f"**{initials(employee['name'])}  {employee['name']}**")
                st.caption(employee["email"])
            with department_column:
                st.markdown(f"**{employee['department']}**")
                st.caption(employee["position"])
            status_column.markdown(f"**{employee['status']}**")
            phone_column.caption(employee.get("phone") or "No phone")
            with actions_column:
                edit_col, delete_col = st.columns(2)
                if edit_col.button("Edit", key=f"edit-{employee['id']}"):
                    st.session_state["editing_employee"] = employee["id"]
                    st.rerun()
                if delete_col.button("Delete", key=f"delete-{employee['id']}"):
                    st.session_state["confirm_delete"] = employee["id"]
                    st.rerun()

if add_clicked:
    st.session_state["editing_employee"] = "new"

editing_id = st.session_state.get("editing_employee")
if editing_id:
    editing_employee = next(
        (employee for employee in employees if employee["id"] == editing_id),
        None,
    )
    is_new = editing_id == "new"
    if is_new or editing_employee:
        with st.form("employee_form", border=True):
            st.subheader("Add a teammate" if is_new else "Edit teammate")
            name_column, email_column = st.columns(2)
            name = name_column.text_input("Full name *", value=editing_employee["name"] if editing_employee else "")
            email = email_column.text_input("Work email *", value=editing_employee["email"] if editing_employee else "")
            department_column, position_column = st.columns(2)
            employee_department = department_column.text_input(
                "Department *",
                value=editing_employee["department"] if editing_employee else "",
            )
            position = position_column.text_input(
                "Job title *",
                value=editing_employee["position"] if editing_employee else "",
            )
            phone_column, status_column = st.columns(2)
            phone = phone_column.text_input("Phone", value=editing_employee.get("phone", "") if editing_employee else "")
            employee_status = status_column.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(editing_employee["status"]) if editing_employee else 0,
            )
            submit_column, cancel_column = st.columns(2)
            submitted = submit_column.form_submit_button(
                "Add employee" if is_new else "Save changes",
                type="primary",
                use_container_width=True,
            )
            canceled = cancel_column.form_submit_button("Cancel", use_container_width=True)
        if canceled:
            st.session_state.pop("editing_employee", None)
            st.rerun()
        if submitted:
            payload = {
                "name": name,
                "email": email,
                "department": employee_department,
                "position": position,
                "phone": phone,
                "status": employee_status,
            }
            try:
                api_request(
                    "POST" if is_new else "PUT",
                    "/api/employees" if is_new else f"/api/employees/{editing_id}",
                    json=payload,
                )
                st.session_state.pop("editing_employee", None)
                st.success("Employee added." if is_new else "Employee updated.")
                st.rerun()
            except RuntimeError as error:
                st.error(str(error))

confirm_delete_id = st.session_state.get("confirm_delete")
if confirm_delete_id:
    employee_to_delete = next(
        (employee for employee in employees if employee["id"] == confirm_delete_id),
        None,
    )
    if employee_to_delete:
        st.warning(f"Remove {employee_to_delete['name']} from the team?")
        confirm_column, cancel_column = st.columns(2)
        if confirm_column.button("Confirm delete", type="primary"):
            try:
                api_request("DELETE", f"/api/employees/{confirm_delete_id}")
                st.session_state.pop("confirm_delete", None)
                st.success("Employee removed.")
                st.rerun()
            except RuntimeError as error:
                st.error(str(error))
        if cancel_column.button("Cancel delete"):
            st.session_state.pop("confirm_delete", None)
            st.rerun()

st.divider()
st.caption(f"Showing {len(filtered_employees)} of {len(employees)} employees  ·  Northstar Studio")
