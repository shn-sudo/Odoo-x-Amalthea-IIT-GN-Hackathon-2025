# Expense Management System

This project is a backend API for handling company expense reimbursements, built during the Odoo x Amalthea Hackathon 2025. It focuses on user management, expense submission, and a multi-step approval workflow.

---

## Features

**Current (Backend API):**
*   **User Management:**
    *   Initial company and admin signup (first user only).
    *   Login with JWT tokens.
    *   Role-based access (Employee, Manager, Admin).
*   **Expense Handling:**
    *   Employees can submit expenses (amount, currency, category, date, description).
    *   Employees can view their submitted expenses.
    *   Managers can view expenses assigned to them for approval.
    *   Managers can approve or reject expenses.
*   **Other:**
    *   Currency conversion for submitted expenses using an external API.
    *   Basic approval workflow assigns expenses to the employee's manager or an admin.
    *   SQLite database with SQLAlchemy ORM.

**Planned (Frontend & More API):**
*   Frontend dashboards with a "Peaky Blinders" aesthetic.
*   Admin panel for managing users and defining approval rules (multi-step, conditional).
*   Receipt upload and potential OCR processing (mentioned as an extra feature in the problem statement, not core).

---

## Tech Stack

*   **Backend:** Python, Flask
*   **Database:** SQLite, SQLAlchemy ORM
*   **Authentication:** JWT, Bcrypt
*   **API Requests:** Requests
*   **Frontend (Planned):** HTML, CSS, JavaScript

---

## Setup

1.  Clone the repo: `git clone <YOUR_REPOSITORY_URL>`
2.  Navigate to the project directory: `cd <YOUR_REPOSITORY_NAME>`
3.  Create a virtual environment: `python -m venv venv`
4.  Activate the virtual environment:
    *   On Windows: `venv\Scripts\activate`
    *   On macOS/Linux: `source venv/bin/activate`
5.  Install dependencies: `pip install -r requirements.txt`
6.  Run the app: `python app.py`
7.  The API should be running on `http://127.0.0.1:5000/`.

---

## API Endpoints (Current)

*   `POST /api/auth/signup`: Create the first admin user and company.
*   `POST /api/auth/login`: User login.
*   `GET /api/protected`: Example protected route.
*   `GET /api/expenses/my`: Get expenses submitted by the logged-in user.
*   `POST /api/expenses/submit`: Submit a new expense.
*   `GET /api/expenses/pending`: Get expenses pending approval for the logged-in manager.
*   `POST /api/expenses/<int:expense_id>/approve`: Approve an expense.
*   `POST /api/expenses/<int:expense_id>/reject`: Reject an expense.

---

## Database Schema

Based on the SQLAlchemy models in `app.py`.

*   `Company`: id, name, base_currency_code, created_at
*   `User`: id, username (unique), email (unique), password_hash, role, company_id (FK), manager_id (self-FK), is_manager_approver, created_at
*   `Expense`: id, amount, original_currency_code, converted_amount, category, description, date, receipt_image_path, status, submitted_by_id (FK), submitted_at, current_approver_id (FK)
*   `Approval`: id, expense_id (FK), approver_id (FK), status, comment, approved_at
*   `ApprovalRule`: id, name, company_id (FK), percentage_required, specific_approver_required_id (FK), is_hybrid_rule, rule_type, sequence_order

---

## Next Steps

1.  Build the frontend interface.
2.  Implement admin user/role management.
3.  Implement full approval rule management.
4.  Add more robust error handling.

---