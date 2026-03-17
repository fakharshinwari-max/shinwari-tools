from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

auth = Blueprint('auth', __name__)

# UNRESTRICTED - Skip login requirement decorator
def optional_login(f):
    """This decorator allows access WITHOUT login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        # REMOVED: Password validation checks
        # REMOVED: Email validation
        # REMOVED: Duplicate email check
        
        # Allow registration with ANY password
        if not name:
            name = 'User'  # Use default name
        if not email:
            email = f'user_{datetime.now().timestamp()}@localhost'  # Auto-generate email
        if not password:
            password = 'password123'  # Default password
        
        hashed = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html', error='')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # REMOVED: Password validation
        user = User.query.filter_by(email=email).first()
        
        # If user doesn't exist, create one automatically
        if not user:
            user = User(name='User', email=email, password=generate_password_hash('password'))
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', error='')

@auth.route('/logout')
# REMOVED: @login_required decorator - anyone can logout
def logout():
    logout_user()
    return redirect(url_for('index'))

# NEW: Allow access to all features WITHOUT login
@auth.route('/bypass-login')
def bypass_login():
    """Quick login without credentials"""
    # Create or get a guest user
    guest = User.query.filter_by(email='guest@localhost').first()
    if not guest:
        guest = User(name='Guest', email='guest@localhost', password=generate_password_hash('guest'))
        db.session.add(guest)
        db.session.commit()
    
    login_user(guest)
    return redirect(url_for('dashboard'))
