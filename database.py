"""
=============================================================================
Module: database.py
Description:
    Central database layer for OZONE. Every CREATE TABLE statement and every
    SQL query in the project lives in this file.

    To add a new table in future:
      1. Append its CREATE TABLE statement to the SCHEMA list below.
      2. Add that table's query functions in a new section underneath.
    init_db() will create it automatically on the next startup.
=============================================================================
"""

import os
import sqlite3
from contextlib import closing

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ozone.db')


# -----------------------------------------------------------------------------
# SCHEMA - every table in the project. Append new tables here.
# -----------------------------------------------------------------------------
SCHEMA = [
    '''
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
    ''',
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates every table listed in SCHEMA. Safe to call on each startup."""
    with closing(get_db()) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        conn.commit()


# -----------------------------------------------------------------------------
# TABLE: farmers
# -----------------------------------------------------------------------------
FARMER_FIELDS = [
    'full_name', 'mobile', 'email', 'password_hash', 'aadhar', 'dob', 'gender',
    'marital_status', 'address', 'state', 'district', 'pincode',
    'land_ownership', 'total_land', 'irrigation_source', 'soil_type',
    'main_crops', 'experience', 'annual_income', 'has_loan', 'loan_amount',
    'bank_name', 'has_kcc', 'monthly_income', 'existing_emi', 'has_insurance',
    'farmer_category', 'is_fpo_member', 'attended_training', 'pref_language',
    'loan_due_date',
]


def email_exists(email):
    with closing(get_db()) as conn:
        row = conn.execute(
            'SELECT id FROM farmers WHERE email = ?', (email,)
        ).fetchone()
    return row is not None


def create_farmer(values):
    """Inserts one farmer. `values` is a dict keyed by FARMER_FIELDS names."""
    columns = ', '.join(FARMER_FIELDS)
    placeholders = ', '.join(['?'] * len(FARMER_FIELDS))
    with closing(get_db()) as conn:
        cursor = conn.execute(
            f'INSERT INTO farmers ({columns}) VALUES ({placeholders})',
            [values.get(field) for field in FARMER_FIELDS]
        )
        conn.commit()
        return cursor.lastrowid


def get_farmer_by_email(email):
    with closing(get_db()) as conn:
        row = conn.execute(
            'SELECT * FROM farmers WHERE email = ?', (email,)
        ).fetchone()
    return dict(row) if row else None


def get_farmer_by_id(farmer_id):
    with closing(get_db()) as conn:
        row = conn.execute(
            'SELECT * FROM farmers WHERE id = ?', (farmer_id,)
        ).fetchone()
    return dict(row) if row else None


def update_loan_due_date(farmer_id, due_date):
    with closing(get_db()) as conn:
        cursor = conn.execute(
            'UPDATE farmers SET loan_due_date = ? WHERE id = ?',
            (due_date, farmer_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def email_exists_for_other(email, farmer_id):
    """Checks whether the given email is already used by a farmer other than farmer_id."""
    with closing(get_db()) as conn:
        row = conn.execute(
            'SELECT id FROM farmers WHERE email = ? AND id != ?', (email, farmer_id)
        ).fetchone()
    return row is not None


def update_farmer_profile(farmer_id, values):
    """
    Updates farmer profile fields in the database.
    Note: Aadhaar (aadhar) is immutable and strictly non-editable once registered.
    """
    editable_fields = [
        'full_name', 'mobile', 'email', 'dob', 'gender',
        'marital_status', 'address', 'state', 'district', 'pincode',
        'land_ownership', 'total_land', 'irrigation_source', 'soil_type',
        'main_crops', 'experience', 'annual_income', 'has_loan', 'loan_amount',
        'bank_name', 'has_kcc', 'monthly_income', 'existing_emi', 'has_insurance',
        'farmer_category', 'is_fpo_member', 'attended_training', 'pref_language',
        'loan_due_date'
    ]

    set_clauses = []
    params = []

    for field in editable_fields:
        if field in values:
            set_clauses.append(f"{field} = ?")
            params.append(values[field])

    if values.get('password_hash'):
        set_clauses.append("password_hash = ?")
        params.append(values['password_hash'])

    if not set_clauses:
        return False

    params.append(farmer_id)
    with closing(get_db()) as conn:
        cursor = conn.execute(
            f"UPDATE farmers SET {', '.join(set_clauses)} WHERE id = ?",
            params
        )
        conn.commit()
        return cursor.rowcount > 0

