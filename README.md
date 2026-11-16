# Northstar Employee Management

A Python employee management app with a FastAPI REST backend, an interactive Streamlit frontend, and a JSON-file database.

## Requirements

- Python 3.10 or newer
- pip

## Install and run

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

In the first terminal, start the API:

```sh
uvicorn backend.main:app --reload
```

In a second terminal, start the Streamlit app:

```sh
streamlit run streamlit_app.py
```

The app opens at [http://localhost:8501](http://localhost:8501). FastAPI's interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Set `EMPLOYEE_API_URL` if the backend is running at a different address; it defaults to `http://127.0.0.1:8000`.

## Database

The employee records are stored in [resources/employees.json](resources/employees.json). The API creates an empty file there if it is missing. Create, update, and delete requests persist their changes to this file.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Check API health |
| `GET` | `/api/employees` | List employees |
| `GET` | `/api/employees/{id}` | Get one employee |
| `POST` | `/api/employees` | Create an employee |
| `PUT` | `/api/employees/{id}` | Update an employee |
| `DELETE` | `/api/employees/{id}` | Delete an employee |

Create and update requests accept JSON with `name`, `email`, `department`, and `position` (required), plus optional `phone` and `status` (`Active`, `On leave`, or `Inactive`). Email addresses must be unique.

The Streamlit interface provides employee creation and editing, deletion with confirmation, text search, department and status filters, and CSV export.
