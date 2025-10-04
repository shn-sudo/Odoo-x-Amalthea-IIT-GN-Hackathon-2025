## **Expense Management System - Hackathon Project**

> **A scalable, clean, and modular solution for automating company expense reimbursement processes.**

**Note:** This project is being developed as part of a hackathon. While AI assistance (like this conversation) is being used as a guide and brainstorming partner, the core goal is to learn, build, and understand the concepts independently. Every effort will be made to research, code, and debug using personal understanding and external resources, with AI input primarily used for structuring ideas and overcoming specific hurdles.

---

### **Project Vision**

To build a robust, user-friendly, and scalable expense management system that eliminates the pain points of manual reimbursement processes. The system will provide transparency, enforce configurable approval workflows, and offer features like OCR for receipts, real-time currency conversion, and detailed audit trails — all while being built from scratch with minimal external dependencies.

---

### **Core Problem Statement**

Companies struggle with manual, error-prone, and opaque expense reimbursement processes. My solution aims to:
- Automate and streamline the submission and approval workflow.
- Provide flexible, rule-based multi-level approvals.
- Ensure data integrity and security through robust design.
- Offer a clean, intuitive UI for all user roles (Admin, Manager, Employee).

---

### **Key Features & User Roles**

#### **1. Authentication & User Management (Admin)**
- **On first signup/login:** A new `Company` record is auto-created. The base currency for the company is set based on the selected country's currency (using the `restcountries.com` API).
- **Admin can:**
  - Create `Employee` and `Manager` users.
  - Assign and change user roles (`Employee`, `Manager`).
  - Define manager-employee relationships (specify which manager is responsible for which employee).
  - Configure complex approval rules (see Conditional Approval Flow section).

#### **2. Expense Submission (Employee)**
- **Employee can:**
  - Submit expense claims with:
    - Amount (in any currency).
    - Category, Description, Date.
    - Option to upload/scan a receipt (OCR integration planned).
  - View their personal expense history (Approved, Rejected, Pending status).

#### **3. Approval Workflow (Manager/Admin)**
- **Key Rule:** An expense is first sent to the employee's designated manager *only if* the manager is flagged as an "approver" (`IS MANAGER APPROVER` field).
- **Sequential Approval:** When multiple approvers are assigned via the `Approval Rule`, the admin defines the *sequence* of approval.
  - Example: `Step 1 → Manager` -> `Step 2 → Finance` -> `Step 3 → Director`.
- **Flow Logic:** An expense moves to the *next* approver in the sequence only after the *current* approver approves or rejects it. The next approver receives an approval request in their account.
- **Manager can:**
  - View expenses waiting for their approval.
  - Approve or Reject an expense, optionally adding comments.
  - See the expense amount converted to the company's default currency in real-time (using the `exchangerate-api.com`).

#### **4. Conditional Approval Flow (Admin Defined)**
- **Approval Rules** support:
  - **Percentage rule:** e.g., "If 60% of the defined approvers approve, the expense is approved."
  - **Specific Approver rule:** e.g., "If the CFO approves, the expense is auto-approved, bypassing others."
  - **Hybrid rule:** Combines both (e.g., "60% OR CFO approves").
- **Combination:** These rules can be combined with the sequential approval flow defined earlier.

#### **5. Role Permissions**

| Role      | Permissions                                                                                      |
| :-------- | :----------------------------------------------------------------------------------------------- |
| **Admin** | Create company (auto on signup), manage users, set roles, configure approval rules, view all expenses, override approvals. |
| **Manager** | Approve/reject expenses (amount visible in company's default currency), view team expenses, escalate as per rules. |
| **Employee** | Submit expenses, view their own expenses, check approval status.                               |

---

### **Technical Requirements & Design Philosophy**

This project prioritizes **scalability**, **clean code**, and **robust architecture** over speed of development. We aim to impress reviewers with our technical depth and attention to detail.

#### **Database Design (Critical!)**
- Use **MySQL** or **PostgreSQL** (local setup preferred).
- Avoid BaaS platforms (Firebase, Supabase, MongoDB Atlas).
- Design normalized, relational tables for Users, Companies, Expenses, Approvals, and Rules.
- Ensure referential integrity and efficient indexing.

#### **Backend API**
- Build a RESTful API from scratch (Node.js/Express, Python/Flask, or similar).
- Implement proper input validation and graceful error handling.
- Use environment variables for sensitive data (API keys, DB credentials).

#### **Frontend UI**
- Clean, responsive, and intuitive design.
- Intuitive navigation for all user roles.
- Interactive elements (e.g., dynamic dropdowns, status indicators).
- Mockups available: [Excalidraw Link](https://link.excalidraw.com/l/65VNwvy7c4X/4WSLZDTrhkA)

#### **Currency Conversion & OCR**
- Use `https://restcountries.com/v3.1/all?fields=name,currencies` for country/currency data.
- Use `https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}` for real-time conversion.
- Implement basic OCR (Tesseract.js or similar) for receipt scanning.

#### **Error Handling & Validation**
- Validate all user inputs (email, password, amounts, dates).
- Provide clear, user-friendly error messages.
- Log errors for debugging purposes.

#### **Version Control & Collaboration**
- Use **Git** for version control.
- Commit frequently with descriptive messages.
- Branching strategy: `main`, `develop`, feature branches.

---

### **Evaluation Criteria (What the Judges Care About)**

| Category             | What to Focus On                                                                 |
|----------------------|------------------------------------------------------------------------------------|
| **Coding Standard**  | Consistent style, meaningful variable names, proper indentation.                  |
| **Logic**            | Clear, efficient algorithms; handle edge cases.                                    |
| **Modularity**       | Break code into reusable, independent modules (e.g., auth, expense, approval).     |
| **Frontend Design**  | Clean, responsive UI; intuitive navigation; accessibility.                         |
| **Performance**      | Optimize queries, minimize API calls, use caching where appropriate.               |
| **Scalability**      | Design for future growth (e.g., multiple companies, thousands of users).           |
| **Security**         | Secure authentication, protect sensitive data, sanitize inputs.                    |
| **Usability**        | Easy for non-technical users; clear feedback; helpful tooltips.                    |
| **Debugging Skills** | Include logging, error handling, and unit tests where possible.                    |
| **Database Design**  | **MOST IMPORTANT!** Well-structured schema, relationships, normalization.          |

---

### **Tools & Technologies (Suggested)**

- **Backend**: Node.js + Express / Python + Flask
- **Frontend**: React / Vue.js / Svelte (or plain HTML/CSS/JS if time-constrained)
- **Database**: PostgreSQL (preferred) or MySQL
- **OCR**: Tesseract.js (JavaScript) or pytesseract (Python)
- **Currency API**: `exchangerate-api.com`
- **Country Data**: `restcountries.com`
- **UI Mockup**: Excalidraw (already provided)
- **Version Control**: Git + GitHub

---

### **Final Notes**

- **Avoid Copy-Paste**: Understand every line of code you write. Know *why* you’re using a library or pattern.
- **Real-Time Data**: Use websockets or polling for live updates (e.g., approval status).
- **AI/Blockchain**: Only include if they genuinely add value (e.g., AI for receipt categorization).
- **Prototype First**: Use static JSON for initial UI mockups, but replace with real DB calls before final submission.

---

### **To End**

Remember, the goal isn’t to build the most complex system, but to build a **well-thought-out, clean, and functional** one that demonstrates your **logical thinking, technical skills, and passion for solving real-world problems**.

