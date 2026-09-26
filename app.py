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