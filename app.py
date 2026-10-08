import os
import sqlite3
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'ozone-smart-farming-secret-key-2026'

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
                    is_fpo_member, attended_training, pref_language
                ) VALUES (
                    'Ramesh Kumar', '9876543210', 'ramesh@kisan.in', ?, '123456789012',
                    '15/08/1982', 'Male / पुरुष', 'Married / विवाहित', 'Village Raikot, Post Pakhowal',
                    'Punjab / पंजाब', 'Ludhiana', '141101', 'Owned / स्वयं का',
                    4.5, 'Canal / नहर', 'Alluvial / जलोढ़', 'Wheat, Paddy, Mustard',
                    15, '₹3,00,000 - ₹5,00,000', 'No / नहीं', '', 'State Bank of India',
                    'Yes / हाँ', '₹35,000', '₹0', 'Yes / हाँ', 'Small / लघु',
                    'Yes / हाँ', 'Yes / हाँ', 'Hindi / हिंदी'
                )
            ''', (demo_password_hash,))
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
                        is_fpo_member, attended_training, pref_language
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    request.form.get('prefLanguage', 'hi')
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
    return render_template('home.html', user=farmer)

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
