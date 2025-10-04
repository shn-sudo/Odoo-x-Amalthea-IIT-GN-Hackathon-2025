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
		access_token = create_access_token(identity=new_user.id)
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


# # Route for user login
# @app.route('/api/auth/login', methods=['POST'])
# def login():
# 	data = request.get_json()
# 	username = data.get('username')
# 	password = data.get('password')

# 	# Find the user by username
# 	user = User.query.filter_by(username=username).first()

# 	# Check if user exists and password is correct
# 	if user and user.check_password(password):
# 		# Generate a JWT token for the authenticated user
# 		access_token = create_access_token(identity=user.id)
# 		return jsonify({
# 			'message': 'Login successful',
# 			'access_token': access_token,
# 			'user_id': user.id,
# 			'role': user.role
# 		}), 200
# 	else:
# 		return jsonify({'message': 'Invalid username or password'}), 401


# # A simple protected route to test authentication
# @app.route('/api/protected', methods=['GET'])
# @jwt_required()
# def protected():
# 	# Get the user ID from the JWT token
# 	current_user_id = get_jwt_identity()
# 	# Fetch the user object from the database
# 	user = User.query.get(current_user_id)
# 	if user:
# 		return jsonify({'message': f'Hello, {user.username}!', 'role': user.role}), 200
# 	else:
# 		return jsonify({'message': 'User not found'}), 404


# --- Main Application Runner ---
# This block ensures the app only runs if this script is executed directly
if __name__ == '__main__':
	# Create the database tables within the application context
	with app.app_context():
		db.create_all()

	# Run the Flask development server
	# debug=True helps with error messages during development
	app.run(debug=True)