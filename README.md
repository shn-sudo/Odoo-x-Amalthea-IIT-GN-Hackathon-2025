# 🎩 Expense Management System 🎩

> **A scalable, clean, and modular backend API solution for automating company expense reimbursement processes.**

---

## 📋 Table of Contents
- [🎯 Project Vision](#-project-vision)
- [✨ Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [⚡ Setup Instructions](#-setup-instructions)
- [🔌 API Endpoints](#-api-endpoints)
- [🗄️ Database Schema](#️-database-schema)
- [🚀 Development Approach](#-development-approach)
- [🔜 Next Steps](#-next-steps)

---

## 🎯 Project Vision

This project aims to build a robust and efficient expense management system. It automates the process of submitting, tracking, and approving employee expenses, streamlining the reimbursement workflow for companies. The backend API provides a secure and scalable foundation for managing user accounts, expense submissions, and multi-step approval workflows, including currency conversion.

*Note: This project was developed with the assistance of AI tools to accelerate learning and development during the hackathon. The goal is to demonstrate logical thinking, technical skills, and a commitment to clean, well-structured code while learning independently.*

---

## ✨ Features

### Current State (Backend API) 🏗️:
- **🔐 Authentication & User Management:**
  - Initial company and admin user signup (first user only).
  - User login with JWT tokens.
  - Employee, Manager, and Admin role-based permissions (enforced via API routes).
- **💸 Expense Management:**
  - Employee can submit new expenses (amount, currency, category, description, date).
  - Employee can view their own submitted expenses.
  - Manager can view expenses pending their approval.
  - Manager can approve or reject expenses.
  - **💱 Currency Conversion:** Submitted expenses are converted to the company's base currency using an external API.
  - **🔄 Basic Approval Workflow:** Expenses are assigned to the employee's direct manager (if marked as an approver) or an admin upon submission. Manager approval/rejection updates the expense status and creates an approval record.
- **💾 Data Management:**
  - SQLite database for local storage and prototyping.
  - SQLAlchemy ORM for database interactions.

### Planned Features (Frontend & Advanced API) 🚀:
- **🎨 Frontend Interface (Peaky Blinders Vibe):**
  - Login/Signup pages.
  - Employee dashboard (submit/view expenses).
  - Manager dashboard (view team expenses, approve/reject pending items).
  - Admin dashboard (manage users, define approval rules).
- **⚙️ Advanced Approval Rules:**
  - Configurable multi-step approval sequences (percentage-based, specific approver, hybrid).
- **📄 Receipt Processing (Optional - Not Core):**
  - *OCR is mentioned as an additional feature in the problem statement but is not implemented in this core API version.*
- **🔔 Notifications:**
  - Alerts for pending approvals, status changes.

---

## 🛠️ Tech Stack

- **Backend:** 🐍 Python, 🌐 Flask
- **Database:** 🗄️ SQLite (for local development), 🐘 SQLAlchemy (ORM)
- **Authentication:** 🔐 JWT (JSON Web Tokens)
- **Password Hashing:** 🔐 Bcrypt
- **API Communication:** 📡 Requests
- **Frontend (Planned):** 💻 HTML, 🎨 CSS, 🧠 JavaScript (Flask templates or potentially a separate framework)

---

## ⚡ Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/shn-sudo/Odoo-x-Amalthea-IIT-GN-Hackathon-2025.git
    cd Odoo-x-Amalthea-IIT-GN-Hackathon-2025
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The application should start on `http://127.0.0.1:5000/`.

---

## 🔌 API Endpoints

### Authentication 🔐
- `POST /api/auth/signup`: Initial admin signup and company creation.
- `POST /api/auth/login`: User login.
- `GET /api/protected`: Example protected route (requires valid JWT).

### Expenses 💸
- `GET /api/expenses/my`: Get expenses submitted by the logged-in user.
- `POST /api/expenses/submit`: Submit a new expense (requires valid JWT).
- `GET /api/expenses/pending`: Get expenses pending approval for the logged-in manager (requires valid JWT).
- `POST /api/expenses/<int:expense_id>/approve`: Approve an expense (requires valid JWT, manager role, and correct `current_approver_id`).
- `POST /api/expenses/<int:expense_id>/reject`: Reject an expense (requires valid JWT, manager role, and correct `current_approver_id`).

---

## 🗄️ Database Schema

*(Based on SQLAlchemy models in `app.py`)*

- **`Company`** 🏢
  - `id` (Primary Key)
  - `name`
  - `base_currency_code`
  - `created_at`
- **`User`** 👤
  - `id` (Primary Key)
  - `username` (Unique)
  - `email` (Unique)
  - `password_hash`
  - `role` (employee, manager, admin)
  - `company_id` (Foreign Key)
  - `manager_id` (Self-referencing Foreign Key)
  - `is_manager_approver`
  - `created_at`
- **`Expense`** 💰
  - `id` (Primary Key)
  - `amount`
  - `original_currency_code`
  - `converted_amount`
  - `category`
  - `description`
  - `date`
  - `receipt_image_path`
  - `status` (pending, approved, rejected)
  - `submitted_by_id` (Foreign Key)
  - `submitted_at`
  - `current_approver_id` (Foreign Key)
- **`Approval`** ✅
  - `id` (Primary Key)
  - `expense_id` (Foreign Key)
  - `approver_id` (Foreign Key)
  - `status` (pending, approved, rejected)
  - `comment`
  - `approved_at`
- **`ApprovalRule`** 📋
  - `id` (Primary Key)
  - `name`
  - `company_id` (Foreign Key)
  - `percentage_required`
  - `specific_approver_required_id` (Foreign Key)
  - `is_hybrid_rule`
  - `rule_type` (percentage, specific, hybrid)
  - `sequence_order`

---

## 🚀 Development Approach

1.  **Start Small, Think Big** 🧠: Began with core authentication and expense submission/retrieval.
2.  **Modular Architecture** 🧱: Separated concerns within `app.py` (Models, Utilities, Routes).
3.  **Test as You Go** 🔬: Used tools like Postman/curl to verify API endpoints.
4.  **Document Everything** 📝: Maintaining this `README.md` and code comments.

---

## 🔜 Next Steps

1.  Complete backend API features (e.g., admin user/role management, admin rule management).
2.  Develop the frontend interface with the "Peaky Blinders vibe".
3.  Implement more complex approval rule logic.
4.  Add comprehensive error handling and logging.
5.  Finalize documentation.

---

*Built with ❤️ during the Odoo x Amalthea, IIT GN Hackathon 2025.*