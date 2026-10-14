import os
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
import sqlite3
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env
load_dotenv()

# Feature Modules
from loan_tracker import (
    get_farmer_loan_tracker_summary,
    calculate_loan_due_days,
    update_farmer_loan_due_date
)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'ozone-smart-farming-secret-key-2026')

database.init_db()


# Weather & Mandi Service Modules
from weather_service import get_weather_and_location, fetch_live_weather
from mandi_service import get_farmer_crop_prices

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ozone.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                aadhar TEXT,
                dob TEXT,
                gender TEXT,
                marital_status TEXT,
                address TEXT,
                state TEXT,
                district TEXT,
                pincode TEXT,
                land_ownership TEXT,
                total_land REAL,
                irrigation_source TEXT,
                soil_type TEXT,
                main_crops TEXT,
                experience INTEGER,
                annual_income TEXT,
                has_loan TEXT,
                loan_amount TEXT,
                bank_name TEXT,
                has_kcc TEXT,
                monthly_income TEXT,
                existing_emi TEXT,
                has_insurance TEXT,
                farmer_category TEXT,
                is_fpo_member TEXT,
                attended_training TEXT,
                pref_language TEXT,
                loan_due_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check and migrate existing tables if loan_due_date column is not present
        cursor.execute("PRAGMA table_info(farmers)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if 'loan_due_date' not in existing_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN loan_due_date TEXT")

        
        # Seed default demo user safely
        cursor.execute('SELECT id FROM farmers WHERE LOWER(email) = ?', ('ramesh@kisan.in',))
        if not cursor.fetchone():
            demo_password_hash = generate_password_hash('password123')
            cursor.execute('''
                INSERT OR IGNORE INTO farmers (
                    full_name, mobile, email, password_hash, aadhar, dob, gender,
                    marital_status, address, state, district, pincode, land_ownership,
                    total_land, irrigation_source, soil_type, main_crops, experience,
                    annual_income, has_loan, loan_amount, bank_name, has_kcc,
                    monthly_income, existing_emi, has_insurance, farmer_category,
                    is_fpo_member, attended_training, pref_language, loan_due_date


                ) VALUES (
                    'Ramesh Kumar', '9876543210', 'ramesh@kisan.in', ?, '123456789012',
                    '15/08/1982', 'Male / पुरुष', 'Married / विवाहित', 'Village Raikot, Post Pakhowal',
                    'Punjab / पंजाब', 'Ludhiana', '141101', 'Owned / स्वयं का',
                    4.5, 'Canal / नहर', 'Alluvial / जलोढ़', 'Wheat, Paddy, Mustard',
                    15, '₹3,00,000 - ₹5,00,000', 'No / नहीं', '', 'State Bank of India',
                    'Yes / हाँ', '₹35,000', '₹0', 'Yes / हाँ', 'Small / लघु',
                    'Yes / हाँ', 'Yes / हाँ', 'Hindi / हिंदी', '2026-10-31'
                )
            ''', (demo_password_hash,))
        else:
            # If demo user exists, make sure loan_due_date is set for testing
            cursor.execute("UPDATE farmers SET loan_due_date = '2026-10-31' WHERE email = 'ramesh@kisan.in' AND (loan_due_date IS NULL OR loan_due_date = '')")

        conn.commit()


# Initialize database on startup
init_db()

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        user = {
            'id': session['user_id'],
            'name': session.get('user_name', 'Farmer'),
            'email': session.get('user_email', '')
        }
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullName', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password or not full_name:
            return render_template('register.html', error="कृपया सभी आवश्यक फ़ील्ड भरें (नाम, ईमेल, पासवर्ड) / Please fill all required fields.")

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM farmers WHERE email = ?', (email,))
                if cursor.fetchone():
                    return render_template('register.html', error="यह ईमेल पहले से पंजीकृत है! कृपया लॉगिन करें / This email is already registered. Please login.")

                pw_hash = generate_password_hash(password)
                cursor.execute('''
                    INSERT INTO farmers (
                        full_name, mobile, email, password_hash, aadhar, dob, gender,
                        marital_status, address, state, district, pincode, land_ownership,
                        total_land, irrigation_source, soil_type, main_crops, experience,
                        annual_income, has_loan, loan_amount, bank_name, has_kcc,
                        monthly_income, existing_emi, has_insurance, farmer_category,
                        is_fpo_member, attended_training, pref_language, loan_due_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    full_name,
                    mobile,
                    email,
                    pw_hash,
                    request.form.get('aadhar', ''),
                    request.form.get('dob', ''),
                    request.form.get('gender', ''),
                    request.form.get('maritalStatus', ''),
                    request.form.get('address', ''),
                    request.form.get('state', ''),
                    request.form.get('district', ''),
                    request.form.get('pincode', ''),
                    request.form.get('landOwnership', ''),
                    float(request.form.get('totalLand', 0) or 0),
                    request.form.get('irrigationSource', ''),
                    request.form.get('soilType', ''),
                    request.form.get('mainCrops', ''),
                    int(request.form.get('experience', 0) or 0),
                    request.form.get('annualIncome', ''),
                    request.form.get('hasLoan', ''),
                    request.form.get('loanAmount', ''),
                    request.form.get('bankName', ''),
                    request.form.get('hasKcc', ''),
                    request.form.get('monthlyIncome', ''),
                    request.form.get('existingEmi', ''),
                    request.form.get('hasInsurance', ''),
                    request.form.get('farmerCategory', ''),
                    request.form.get('isFpoMember', ''),
                    request.form.get('attendedTraining', ''),
                    request.form.get('prefLanguage', 'hi'),
                    request.form.get('loanDueDate', '')
                ))
                user_id = cursor.lastrowid
                conn.commit()

            # Set session
            session['user_id'] = user_id
            session['user_name'] = full_name
            session['user_email'] = email

            return render_template('register.html', success=True, farmer_name=full_name)
        except Exception as e:
            return render_template('register.html', error=f"पंजीकरण में त्रुटि / Registration error: {str(e)}")

    return render_template('register.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form.to_dict() or {}
    email = data.get('email', data.get('username', '')).strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and Password are required / ईमेल और पासवर्ड आवश्यक हैं।"
        }), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, full_name, email, password_hash FROM farmers WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']

                return jsonify({
                    "status": "success",
                    "message": f"Welcome back, {user['full_name']}! / आपका स्वागत है!",
                    "user": {
                        "id": user['id'],
                        "name": user['full_name'],
                        "email": user['email']
                    }
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid email or password / गलत ईमेल या पासवर्ड दर्ज किया गया है।"
                }), 401
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/user')
def api_user():
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session['user_id'],
                "name": session.get('user_name', 'Farmer'),
                "email": session.get('user_email', '')
            }
        })
    return jsonify({"logged_in": False, "user": None})

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM farmers WHERE id = ?', (session['user_id'],))
        row = cursor.fetchone()
        if not row:
            session.clear()
            return redirect(url_for('index'))
        farmer = dict(row)
        farmer['name'] = farmer.get('full_name', session.get('user_name', 'Farmer'))
      
        # Feature: Loan Due Tracker
        loan_tracker = get_farmer_loan_tracker_summary(farmer)
        
    return render_template('home.html', user=farmer, loan_tracker=loan_tracker)

    farmer_district = (farmer.get('district') or 'Ludhiana').split('/')[0].strip()
    farmer_state = (farmer.get('state') or 'Punjab').split('/')[0].strip()
    initial_weather = get_weather_and_location(default_city=farmer_district, default_state=farmer_state)
    mandi_prices = get_farmer_crop_prices(farmer.get('state'), farmer.get('main_crops'))

    return render_template(
        'home.html',
        user=farmer,
        loan_tracker=loan_tracker,
        weather=initial_weather,
        mandi_prices=mandi_prices
    )


@app.route('/api/weather', methods=['GET'])
def api_weather():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    city = request.args.get('city', type=str)
    state = request.args.get('state', type=str)

    # If state or city not passed in query, inspect logged-in farmer
    if 'user_id' in session:
        farmer = database.get_farmer_by_id(session['user_id'])
        if farmer:
            if not city and not (lat is not None and lon is not None):
                city = farmer.get('district')
            if not state:
                state = farmer.get('state')

    default_city = (city or 'Ludhiana').split('/')[0].strip()
    default_state = (state or '').split('/')[0].strip() if state else None
    data = get_weather_and_location(lat=lat, lon=lon, default_city=default_city, default_state=default_state)
    return jsonify(data)


@app.route('/api/mandi-prices', methods=['GET'])
def api_mandi_prices():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    farmer = database.get_farmer_by_id(session['user_id'])
    if not farmer:
        return jsonify({'status': 'error', 'message': 'Farmer not found'}), 404
    prices = get_farmer_crop_prices(farmer.get('state'), farmer.get('main_crops'))
    return jsonify({'status': 'success', 'prices': prices})


@app.route('/farmer-profile', methods=['GET', 'POST'])
@app.route('/profile', methods=['GET', 'POST'])
def farmer_profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    farmer_id = session['user_id']
    farmer = database.get_farmer_by_id(farmer_id)
    if not farmer:
        session.clear()
        return redirect(url_for('index'))

    error = None
    success = None

    if request.method == 'POST':
        full_name = request.form.get('fullName', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not full_name or not mobile or not email:
            error = "कृपया सभी आवश्यक फ़ील्ड भरें (नाम, मोबाइल, ईमेल) / Please fill all required fields."
        elif database.email_exists_for_other(email, farmer_id):
            error = "यह ईमेल पहले से किसी अन्य खाते में पंजीकृत है! / This email is already registered with another account."
        else:
            try:
                update_data = {
                    'full_name': full_name,
                    'mobile': mobile,
                    'email': email,
                    'dob': request.form.get('dob', '').strip(),
                    'gender': request.form.get('gender', '').strip(),
                    'marital_status': request.form.get('maritalStatus', '').strip(),
                    'address': request.form.get('address', '').strip(),
                    'state': request.form.get('state', '').strip(),
                    'district': request.form.get('district', '').strip(),
                    'pincode': request.form.get('pincode', '').strip(),
                    'land_ownership': request.form.get('landOwnership', '').strip(),
                    'total_land': float(request.form.get('totalLand', 0) or 0),
                    'irrigation_source': request.form.get('irrigationSource', '').strip(),
                    'soil_type': request.form.get('soilType', '').strip(),
                    'main_crops': request.form.get('mainCrops', '').strip(),
                    'experience': int(request.form.get('experience', 0) or 0),
                    'annual_income': request.form.get('annualIncome', '').strip(),
                    'has_loan': request.form.get('hasLoan', '').strip(),
                    'loan_amount': request.form.get('loanAmount', '').strip(),
                    'bank_name': request.form.get('bankName', '').strip(),
                    'has_kcc': request.form.get('hasKcc', '').strip(),
                    'monthly_income': request.form.get('monthlyIncome', '').strip(),
                    'existing_emi': request.form.get('existingEmi', '').strip(),
                    'has_insurance': request.form.get('hasInsurance', '').strip(),
                    'farmer_category': request.form.get('farmerCategory', '').strip(),
                    'is_fpo_member': request.form.get('isFpoMember', '').strip(),
                    'attended_training': request.form.get('attendedTraining', '').strip(),
                    'pref_language': request.form.get('prefLanguage', 'hi').strip(),
                    'loan_due_date': request.form.get('loanDueDate', '').strip(),
                }

                if password:
                    update_data['password_hash'] = generate_password_hash(password)

                database.update_farmer_profile(farmer_id, update_data)

                # Keep session in sync with updated name and email
                session['user_name'] = full_name
                session['user_email'] = email

                # Reload updated record from database
                farmer = database.get_farmer_by_id(farmer_id)
                success = "किसान प्रोफ़ाइल सफलतापूर्वक अपडेट हो गई है! / Farmer profile updated successfully in database!"
            except Exception as e:
                error = f"अपडेट में त्रुटि / Update error: {str(e)}"

    return render_template('farmer_profile.html', farmer=farmer, error=error, success=success)



# =========================================================================
# FEATURE MODULE: Loan Due Tracker 
# =========================================================================
@app.route('/api/loan-tracker/update', methods=['POST'])
def api_update_loan_tracker():
    """
    Dedicated endpoint contributed by Shrim:
    Allows farmer to update their next loan EMI due date directly from the dashboard
    and immediately recalculates days remaining, status color, and ring offsets.
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    
    data = request.get_json() or request.form.to_dict() or {}
    new_due_date = data.get('dueDate', '').strip()
    
    if not new_due_date:
        return jsonify({'status': 'error', 'message': 'Please provide a valid due date'}), 400
        
    try:
        with get_db() as conn:
            success = update_farmer_loan_due_date(conn, session['user_id'], new_due_date)
            if not success:
                return jsonify({'status': 'error', 'message': 'Failed to update due date in database'}), 500
                
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM farmers WHERE id = ?', (session['user_id'],))
            farmer = dict(cursor.fetchone())
            
        tracker_data = get_farmer_loan_tracker_summary(farmer)
        return jsonify({'status': 'success', 'tracker': tracker_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or not password:
            return redirect(url_for('index'))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, full_name, email, password_hash FROM farmers WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']
                return redirect(url_for('home'))
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
