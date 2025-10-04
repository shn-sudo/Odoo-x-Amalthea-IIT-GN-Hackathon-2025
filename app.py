# Import necessary libraries from Flask and other packages
from flask import Flask, request, jsonify
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
