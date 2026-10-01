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