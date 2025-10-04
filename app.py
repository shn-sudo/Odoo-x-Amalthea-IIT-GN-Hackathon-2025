# Import necessary libraries from Flask and other packages
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests
import os
from datetime import datetime

# --- Application Setup ---
# Create the Flask application instance
app = Flask(__name__)

# Configure the database URI (where to store the SQLite file)
# os.path.join ensures the path works on different operating systems
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'expenses.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Turn off a feature we don't need, avoids warnings

# Configure JWT (for secure login)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-in-production' # Use a strong, random key in real projects

# Initialize the extensions with the Flask app
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- Database Models (Tables Definition) ---
# These define the structure of our data in the database

# Company Table
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_currency_code = db.Column(db.String(3), nullable=False) # e.g., 'USD', 'EUR'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: A company has many users
    users = db.relationship('User', backref='company', lazy=True, cascade="all, delete-orphan")

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee') # 'admin', 'manager', 'employee'
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Self-referencing for manager
    is_manager_approver = db.Column(db.Boolean, default=False) # For approval workflow
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referencing relationship for manager/employee
    manager = db.relationship('User', remote_side=[id], backref='subordinates')

    # Method to hash and set the password
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Method to check if the provided password matches the hash
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# --- API Routes (Endpoints) ---

# Route for user signup (handles initial company creation too)
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    # Get the JSON data sent by the user
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    company_name = data.get('company_name') # Required only for first signup
    country_name = data.get('country')      # Required only for first signup
    # --- Logic for First Signup ---
    # Check if any company already exists in the database
    first_company_exists = Company.query.first() is not None

    if first_company_exists:
        # If a company exists, this endpoint is not for creating the first one
        return jsonify({'message': 'A company already exists. This endpoint is for the initial signup only.'}), 400

    # Validate required fields for the first signup
    if not company_name or not country_name:
        return jsonify({'message': 'Company name and country are required for the first signup.'}), 400

    # --- Fetch Currency Code from External API ---
    try:
        country_api_url = f"https://restcountries.com/v3.1/name/{country_name}?fields=currencies"
        response = requests.get(country_api_url)
        if response.status_code == 200:
            country_data = response.json()
            if country_data:
                # Get the first currency code from the API response
                currency_dict = country_data[0].get('currencies', {})
                if currency_dict:
                    base_currency_code = list(currency_dict.keys())[0] # e.g., 'USD'
                else:
                    return jsonify({'message': 'Currency information not found for the country.'}), 400
            else:
                return jsonify({'message': 'Country not found in the API.'}), 400
        else:
            return jsonify({'message': 'Failed to fetch currency data from API.'}), 500
    except Exception as e:
        print(f"Error fetching currency: {e}") # Log error for debugging
        return jsonify({'message': 'An error occurred while fetching currency data.'}), 500

    # --- Create Company and Admin User ---
    # Hash the user's password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create the new Company record
    new_company = Company(name=company_name, base_currency_code=base_currency_code)

    # Create the new Admin User record
    new_user = User(
        username=username,
        email=email,
        role='admin', # First user is always admin
        company=new_company # Associate user with the new company
    )
    new_user.set_password(password) # Use the method to hash and set the password

    # Add both records to the database session
    db.session.add(new_company)
    # The user is automatically added because of the relationship and cascade="all, delete-orphan"
    # Or you can explicitly add it: db.session.add(new_user)

    try:
        # Commit the transaction to save changes to the database file
        db.session.commit()
        # Generate a JWT token for the new admin user
        access_token = create_access_token(identity=str(new_user.id))
        return jsonify({
            'message': 'Admin user and company created successfully!',
            'access_token': access_token,
            'user_id': new_user.id,
            'company_id': new_company.id
        }), 201
    except Exception as e:
        # If something goes wrong, undo the changes made in this session
        db.session.rollback()
        print(f"Database error during signup: {e}") # Log error for debugging
        return jsonify({'message': 'An error occurred while creating the user or company.'}), 500


# Route for user login
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find the user by username
    user = User.query.filter_by(username=username).first()

    # Check if user exists and password is correct
    if user and user.check_password(password):
        # Generate a JWT token for the authenticated user
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user_id': user.id,
            'role': user.role
        }), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401


# A simple protected route to test authentication
@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    # Get the user ID from the JWT token
    current_user_id = int(get_jwt_identity())
    # Fetch the user object from the database
    user = User.query.get(current_user_id)
    if user:
        return jsonify({'message': f'Hello, {user.username}!', 'role': user.role}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Define the Expense Model (add this *before* the routes if not already defined elsewhere)
# We need to add this model to represent an expense in the database
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False) # Amount of the expense
    original_currency_code = db.Column(db.String(3), nullable=False) # Currency the expense was submitted in
    converted_amount = db.Column(db.Float, nullable=True) # Amount converted to company currency
    category = db.Column(db.String(100), nullable=False) # e.g., Travel, Food, Supplies
    description = db.Column(db.Text, nullable=True) # Description of the expense
    date = db.Column(db.Date, nullable=False) # Date of the expense
    receipt_image_path = db.Column(db.String(255), nullable=True) # Path to uploaded receipt image (optional for now)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'approved', 'rejected'
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Link to the employee who submitted
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow) # When it was submitted
    current_approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Link to the manager currently responsible for approval

    # Relationship to the User who submitted it - FIXED: Added foreign_keys
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id], backref='submitted_expenses')
    # Relationship to the User who is the current approver - ADDED: Added foreign_keys
    current_approver = db.relationship('User', foreign_keys=[current_approver_id], backref='expenses_to_approve')

    # Relationship to Approval records (we'll define this model later)
    approvals = db.relationship('Approval', backref='expense', lazy=True, cascade="all, delete-orphan")


# Define the Approval Model (add this *before* the routes if not already defined elsewhere)
# This model will track the approval status for each step in the workflow
class Approval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'approved', 'rejected'
    comment = db.Column(db.Text, nullable=True) # Optional comment from the approver
    approved_at = db.Column(db.DateTime, nullable=True) # When it was approved/rejected

    # Relationships
    approver = db.relationship('User', backref='approvals_given')


# Define the ApprovalRule Model (add this *before* the routes if not already defined elsewhere)
# This model will store the rules defined by the admin for conditional approvals
class ApprovalRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g., "Standard Rule", "High Value Rule"
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False) # Link to the company
    percentage_required = db.Column(db.Integer, nullable=True) # e.g., 60 for 60%
    specific_approver_required_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # e.g., CFO ID
    is_hybrid_rule = db.Column(db.Boolean, default=False) # If True, combines percentage and specific approver
    rule_type = db.Column(db.String(20), nullable=False) # 'percentage', 'specific', 'hybrid'
    sequence_order = db.Column(db.Integer, nullable=False) # Order in the approval sequence

    # Relationship to the company
    company = db.relationship('Company', backref='approval_rules')

    # Relationship to the specific required approver
    specific_approver_required = db.relationship('User')


# --- Utility Functions ---

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another using an external API."""
    if from_currency == to_currency:
        return amount

    try:
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}")
        if response.status_code == 200:
            data = response.json()
            rate = data['rates'].get(to_currency)
            if rate:
                return round(amount * rate, 2)
            else:
                print(f"Warning: Conversion rate for {to_currency} not found in API response for {from_currency}")
                return amount # Fallback to original amount if rate not found
        else:
            print(f"Warning: Failed to fetch conversion rate from API. Status code: {response.status_code}")
            return amount # Fallback to original amount if API call fails
    except Exception as e:
        print(f"Error converting currency: {e}")
        return amount # Fallback to original amount on exception


# --- API Routes (Endpoints) ---

# Route for employee to view their own submitted expenses
@app.route('/api/expenses/my', methods=['GET'])
@jwt_required() # Requires a valid JWT token
def view_my_expenses():
    # Get the user ID from the JWT token
    current_user_id = int(get_jwt_identity()) # Convert string identity back to int

    # Query the database for expenses submitted by the current user
    # Order by submission date, newest first
    user_expenses = Expense.query.filter_by(submitted_by_id=current_user_id).order_by(Expense.submitted_at.desc()).all()

    # Prepare the response data
    expenses_list = []
    for expense in user_expenses:
        expenses_list.append({
            'id': expense.id,
            'amount': expense.amount,
            'original_currency_code': expense.original_currency_code,
            'converted_amount': expense.converted_amount, # Include converted amount
            'category': expense.category,
            'description': expense.description,
            'date': expense.date.isoformat(), # Convert date object to string
            'status': expense.status,
            'submitted_at': expense.submitted_at.isoformat() # Convert datetime object to string
        })

    return jsonify({
        'message': 'Expenses retrieved successfully',
        'expenses': expenses_list
    }), 200

# Route for employee to submit an expense
@app.route('/api/expenses/submit', methods=['POST'])
@jwt_required() # Requires a valid JWT token
def submit_expense():
    # Get the user ID from the JWT token
    current_user_id = int(get_jwt_identity()) # Convert string identity back to int
    current_user = User.query.get(current_user_id)

    if not current_user:
         return jsonify({'message': 'User not found'}), 404

    # Get the JSON data sent by the user
    data = request.get_json()
    amount = data.get('amount')
    original_currency_code = data.get('original_currency_code', 'USD') # Default to USD if not provided
    category = data.get('category')
    description = data.get('description', '') # Default to empty string
    date_str = data.get('date') # Expecting date in YYYY-MM-DD format

    # Validate required fields
    if not amount or not category or not date_str:
        return jsonify({'message': 'Amount, category, and date are required.'}), 400

    # Convert date string to date object
    try:
        from datetime import datetime # Import inside function if not at top level
        expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Optional: Validate amount is positive
    if amount <= 0:
        return jsonify({'message': 'Amount must be greater than zero.'}), 400

    # --- Currency Conversion ---
    company = Company.query.get(current_user.company_id)
    converted_amount = convert_currency(amount, original_currency_code, company.base_currency_code)

    # Create the new Expense record
    new_expense = Expense(
        amount=amount,
        original_currency_code=original_currency_code,
        converted_amount=converted_amount, # Store the converted amount
        category=category,
        description=description,
        date=expense_date,
        submitted_by_id=current_user.id, # Link the expense to the logged-in user
        status='pending' # Initial status is pending
    )

    # --- Assign Initial Approver (Simple Logic) ---
    # For now, assign to the direct manager if they are an approver, otherwise to an admin
    if current_user.manager and current_user.manager.is_manager_approver:
        new_expense.current_approver_id = current_user.manager_id
    else:
        # Find the first admin user in the company
        admin_user = User.query.filter_by(company_id=current_user.company_id, role='admin').first()
        if admin_user:
            new_expense.current_approver_id = admin_user.id
        # If no admin found, current_approver_id remains None, which might need handling

    # Add the expense to the database session
    db.session.add(new_expense)

    try:
        # Commit the transaction to save the expense
        db.session.commit()
        return jsonify({
            'message': 'Expense submitted successfully!',
            'expense_id': new_expense.id,
            'status': new_expense.status,
            'current_approver_id': new_expense.current_approver_id # Return the assigned approver ID
        }), 201
    except Exception as e:
        # If something goes wrong, undo the changes made in this session
        db.session.rollback()
        print(f"Database error during expense submission: {e}") # Log error for debugging
        return jsonify({'message': 'An error occurred while submitting the expense.'}), 500

# Route for manager to view expenses pending their approval
@app.route('/api/expenses/pending', methods=['GET'])
@jwt_required() # Requires a valid JWT token
def view_pending_expenses():
    # Get the user ID from the JWT token (the manager's ID)
    current_manager_id = int(get_jwt_identity()) # Convert string identity back to int

    # Query the database for expenses where the current user is the current_approver_id and status is pending
    pending_expenses = Expense.query.filter_by(current_approver_id=current_manager_id, status='pending').all()

    # Prepare the response data
    expenses_list = []
    for expense in pending_expenses:
        # Fetch the employee's name who submitted it for better context
        submitted_by_user = User.query.get(expense.submitted_by_id)
        expenses_list.append({
            'id': expense.id,
            'amount': expense.amount,
            'original_currency_code': expense.original_currency_code,
            'converted_amount': expense.converted_amount,
            'category': expense.category,
            'description': expense.description,
            'date': expense.date.isoformat(), # Convert date object to string
            'status': expense.status,
            'submitted_by_id': expense.submitted_by_id, # Include the ID of the submitter
            'submitted_by_username': submitted_by_user.username if submitted_by_user else 'Unknown', # Include the submitter's username
            'submitted_at': expense.submitted_at.isoformat() # Convert datetime object to string
        })

    return jsonify({
        'message': 'Pending expenses retrieved successfully',
        'expenses': expenses_list
    }), 200

# Route for manager to approve an expense
@app.route('/api/expenses/<int:expense_id>/approve', methods=['POST'])
@jwt_required()
def approve_expense(expense_id):
    # Get the manager's ID from the JWT token
    current_manager_id = int(get_jwt_identity())

    # Get the expense from the database
    expense = Expense.query.get_or_404(expense_id) # Returns 404 if expense doesn't exist

    # Check if the current user is the *current* approver for this expense
    if expense.current_approver_id != current_manager_id:
        return jsonify({'message': 'You are not authorized to approve this expense.'}), 403

    # Check if the expense is still pending
    if expense.status != 'pending':
        return jsonify({'message': f'Expense is already {expense.status}.'}), 400

    # Get optional comment from request body
    data = request.get_json()
    comment = data.get('comment', '') # Default to empty string if no comment provided

    # --- Create an Approval Record ---
    new_approval = Approval(
        expense_id=expense.id,
        approver_id=current_manager_id,
        status='approved',
        comment=comment,
        approved_at=datetime.utcnow()
    )
    db.session.add(new_approval)

    # --- Update the Expense Status ---
    # For now, let's assume approving finalizes the expense.
    # In a full workflow, this is where you'd check rules and assign the next approver.
    expense.status = 'approved'
    expense.current_approver_id = None # No more approver needed after final approval

    try:
        # Commit the changes to the database
        db.session.commit()
        return jsonify({
            'message': 'Expense approved successfully.',
            'expense_id': expense.id,
            'new_status': expense.status
        }), 200
    except Exception as e:
        # If something goes wrong, undo the changes made in this session
        db.session.rollback()
        print(f"Database error during approval: {e}") # Log error for debugging
        return jsonify({'message': 'An error occurred while processing the approval.'}), 500

# Route for manager to reject an expense
@app.route('/api/expenses/<int:expense_id>/reject', methods=['POST'])
@jwt_required()
def reject_expense(expense_id):
    # Get the manager's ID from the JWT token
    current_manager_id = int(get_jwt_identity())

    # Get the expense from the database
    expense = Expense.query.get_or_404(expense_id) # Returns 404 if expense doesn't exist

    # Check if the current user is the *current* approver for this expense
    if expense.current_approver_id != current_manager_id:
        return jsonify({'message': 'You are not authorized to reject this expense.'}), 403

    # Check if the expense is still pending
    if expense.status != 'pending':
        return jsonify({'message': f'Expense is already {expense.status}.'}), 400

    # Get comment from request body (required for rejection)
    data = request.get_json()
    comment = data.get('comment')
    if not comment:
        return jsonify({'message': 'A comment is required for rejection.'}), 400

    # --- Create an Approval Record ---
    new_approval = Approval(
        expense_id=expense.id,
        approver_id=current_manager_id,
        status='rejected',
        comment=comment,
        approved_at=datetime.utcnow()
    )
    db.session.add(new_approval)

    # --- Update the Expense Status ---
    expense.status = 'rejected'
    expense.current_approver_id = None # No more approver needed after rejection

    try:
        # Commit the changes to the database
        db.session.commit()
        return jsonify({
            'message': 'Expense rejected successfully.',
            'expense_id': expense.id,
            'new_status': expense.status
        }), 200
    except Exception as e:
        # If something goes wrong, undo the changes made in this session
        db.session.rollback()
        print(f"Database error during rejection: {e}") # Log error for debugging
        return jsonify({'message': 'An error occurred while processing the rejection.'}), 500

# --- Frontend Routes (Flask Templates) ---
# These routes render the HTML pages for the frontend

@app.route('/')
def index():
    # If user is logged in, redirect to their dashboard
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'manager':
            return redirect(url_for('manager_dashboard'))
        else: # employee
            return redirect(url_for('employee_dashboard'))
    # If not logged in, show the login page
    return render_template('login.html')

@app.route('/login')
def login_page():
    # Show the login page
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    # Show the signup page
    # Only allow signup if no company exists (first admin signup)
    if Company.query.first():
        return redirect(url_for('login_page'))
    return render_template('signup.html')

@app.route('/employee')
def employee_dashboard():
    # Check if user is logged in and is an employee
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('index'))
    # Fetch user's expenses
    user_expenses = Expense.query.filter_by(submitted_by_id=session['user_id']).order_by(Expense.submitted_at.desc()).all()
    return render_template('employee_dashboard.html', expenses=user_expenses)

@app.route('/manager')
def manager_dashboard():
    # Check if user is logged in and is a manager
    if 'user_id' not in session or session['role'] != 'manager':
        return redirect(url_for('index'))
    # Fetch pending expenses assigned to the current manager
    pending_expenses = Expense.query.filter_by(current_approver_id=session['user_id'], status='pending').all()
    # Fetch all expenses submitted by subordinates (optional view)
    subordinate_ids = [u.id for u in User.query.filter_by(manager_id=session['user_id']).all()]
    team_expenses = Expense.query.filter(Expense.submitted_by_id.in_(subordinate_ids)).all()
    return render_template('manager_dashboard.html', pending_expenses=pending_expenses, team_expenses=team_expenses)

@app.route('/admin')
def admin_dashboard():
    # Check if user is logged in and is an admin
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    # Fetch all users in the company
    company_users = User.query.filter_by(company_id=session['company_id']).all()
    # Fetch all expenses in the company
    all_expenses = Expense.query.all()
    return render_template('admin_dashboard.html', users=company_users, expenses=all_expenses)

@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('index'))

# --- Main Application Runner ---
# This block ensures the app only runs if this script is executed directly
if __name__ == '__main__':
    # Create the database tables within the application context
    with app.app_context():
        db.create_all()

    # Run the Flask development server
    # debug=True helps with error messages during development
    app.run(debug=True)