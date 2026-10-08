# 🌾 OZONE — Smart Agriculture & Agri-Fintech Platform

> **Final Year Engineering Capstone Project**  
> *An integrated, AI-assisted platform empowering Indian farmers with live IoT telemetry, market intelligence, credit tracking, and precision agronomy.*

---

## 📌 Project Overview

**OZONE** is an end-to-end Smart Agriculture and Agri-Fintech ecosystem designed to bridge the gap between traditional Indian farming and modern digital agriculture. Built with a focus on simplicity, bilingual accessibility (Hindi & English), and actionable data, OZONE brings together:

- **Precision Agronomy**: Real-time IoT sensor telemetry (soil moisture, temperature, pH, NPK levels).
- **Market Intelligence**: Crop mandi price forecasting with actionable buy/hold/sell recommendations.
- **Agri-Fintech & Credit Tracking**: Dynamic loan repayment trackers, EMI countdowns, and KCC management.
- **National Farmer Registry**: Comprehensive 4-tier farmer profiling complying with national agricultural database standards.
- **Scheme Advisory**: Direct matching with central and state government farmer welfare schemes.

---

## 👥 Team & Module Contributions

This project is developed as a collaborative final year team project. Each module is built with modular separation so team members can independently develop, test, and commit their respective features to Git.

| Contributor | Feature / Module | Dedicated Files / Functions | Status |
| :--- | :--- | :--- | :--- |
| **Shrim** | **Loan Due Tracker & Credit Advisory** | `loan_tracker.py`, `/api/loan-tracker/update`, `home.html` (Loan Tracker Panel & Dynamic Modal) | ✅ Completed |
| **Team** | **Farmer Registration & Profiles** | `templates/register.html`, `static/css/register.css`, `/register` route | ✅ Completed |
| **Team** | **Landing Page & Authentication** | `templates/index.html`, `static/js/main.js`, `/api/login`, `/logout` | ✅ Completed |
| **Team** | **Kisan Dashboard UI & Architecture** | `templates/home.html`, `static/css/home.css`, `/home` | ✅ Completed |
| *Upcoming* | *AI Crop Disease Detection (CV)* | Image inference pipeline & disease remedies | ⏳ In Progress |
| *Upcoming* | *Live Mandi API & Historical Analytics* | Agmarknet data scraping / automated sync | ⏳ In Progress |

---

## 🚀 Key Features Implemented

### 1. 💳 Loan Due Tracker & EMI Countdown (*Contributed by Shrim*)
- **Automated Due Date Calculation**: Computes exact days remaining until the next loan or EMI installment directly from registration or profile updates.
- **Intelligent Urgency Categorization**:
  - 🟢 **Safe / On Track** (`> 10 days`): Emerald indicator with reminder scheduling.
  - 🟡 **Warning / Upcoming** (`4 - 10 days`): Amber indicator advising liquidity management.
  - 🟠 **Urgent Action** (`1 - 3 days`): High-priority prompt to avoid default charges.
  - 🔴 **Due Today / Overdue** (`<= 0 days`): Real-time alert with bank contact notices.
- **Interactive SVG Gauge**: Animated circular progress ring dynamically recalculates its `stroke-dashoffset` and accent colors based on repayment countdown.
- **Real-Time Date Adjustment**: In-dashboard modal allowing farmers and evaluators to update their due date and observe instant live updates without full page reloads.

### 2. 📊 Executive Kisan Dashboard
- **5 Comprehensive KPI Gauges**:
  1. *Composite Farm Risk Score* (0–100 calibrated index).
  2. *Crop Health Index* (Vegetative vigor status).
  3. *Mandi Spot Price* (Current crop benchmark price).
  4. *Eligible Govt Schemes* (Custom scheme match count).
  5. *Active Loan Summary* (Outstanding principal and bank affiliation).
- **Mandi Price Forecast Chart**: HTML5 Canvas smooth cubic-bezier curve plotting 7-day predicted commodity prices with intelligent "Hold / Sell" advisory.
- **IoT Field Telemetry**: Live sensor readings for Soil Moisture (%), Ambient Temperature (°C), Humidity (%), Soil pH, and NPK Nitrogen-Phosphorus-Potassium ratios.
- **Actionable Agronomy Feed**: Dynamic irrigation advisories, pest warnings, and PM-Kisan eKYC compliance deadlines.
- **Quick Action Hub**: 1-click access to Crop Doctor, KCC Loan applications, Soil Health Cards, and Mandi price lookups.

### 3. 📝 Comprehensive National Farmer Registration
- Standardized 4-step wizard:
  1. **Personal Identity**: Aadhar, DOB, gender, marital status, contact info.
  2. **Land & Cultivation Profile**: Land ownership (Owned/Leased), acreage, canal/borewell irrigation, soil taxonomy, principal crops, and annual farming income.
  3. **Financial & Credit Record**: Active crop loans, loan amount, **Next EMI due date**, primary bank, KCC ownership, monthly revenue, EMI outflow, and PMFBY insurance.
  4. **Categorization & Preferences**: Small/Marginal classification, FPO membership, agricultural training, and language choice.

### 4. 🔐 Authentication & Session Security
- Secure registration and login backed by Werkzeug password hashing (`generate_password_hash`, `check_password_hash`).
- Flash messaging and modal login supporting seamless session rehydration.
- Pre-seeded demo account for evaluation: `ramesh@kisan.in` / `password123`.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ with [Flask 3.0](https://flask.palletsprojects.com/)
- **Security**: Werkzeug (`generate_password_hash`, `check_password_hash`)
- **Database**: SQLite 3 with automatic schema migration checks
- **Frontend Architecture**:
  - Semantic HTML5 with bilingual localization (Hindi & English)
  - Custom Modular CSS (Vanilla CSS3 Design System with HSL color tokens, glassmorphism, responsive grid layouts)
  - Vanilla JavaScript & HTML5 Canvas API (No heavy framework dependencies)
  - Typography: Google Fonts (*Plus Jakarta Sans*, *Outfit*, *Inter*)

---

## 📁 Repository Directory Structure

```text
├── app.py                     # Main Flask application, routing & session handlers
├── loan_tracker.py            # [Shrim's Module] Loan calculation, urgency state, & APIs
├── ozone.db                   # SQLite database (auto-initialized on startup)
├── requirements.txt           # Python dependency specifications
├── README.md                  # Complete project documentation
│
├── templates/
│   ├── index.html             # Landing page with hero, features, and login modal
│   ├── home.html              # Farmer dashboard, KPI gauges, IoT panel & Loan Tracker
│   └── register.html          # 4-step comprehensive farmer registration portal
│
├── static/
│   ├── css/
│   │   ├── style.css          # Landing page styles & responsive design
│   │   ├── home.css           # Dashboard design system, panels, gauges & modal
│   │   └── register.css       # Registration wizard layout & grid inputs
│   │
│   ├── js/
│   │   └── main.js            # Landing page navigation, login modal & animations
│   │
│   └── images/                # High-res graphics, logo & UI preview assets
```

---

## 🗄️ Database Schema (`farmers` Table)

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Auto-incrementing unique farmer identifier |
| `full_name` | `TEXT NOT NULL` | Farmer's legal full name |
| `mobile` | `TEXT NOT NULL` | Primary mobile number |
| `email` | `TEXT UNIQUE NOT NULL` | Unique account email for login |
| `password_hash` | `TEXT NOT NULL` | Werkzeug salted cryptographic password hash |
| `aadhar` | `TEXT` | 12-digit Aadhar identification |
| `dob` / `gender` | `TEXT` | Date of birth & gender |
| `address` / `state` / `district` | `TEXT` | Geographic location details |
| `pincode` | `TEXT` | Postal index number |
| `land_ownership` | `TEXT` | Owned / Leased / Sharecropper |
| `total_land` | `REAL` | Cultivable landholding in acres |
| `irrigation_source` | `TEXT` | Canal, Tube well, Rainfed, etc. |
| `soil_type` / `main_crops` | `TEXT` | Soil characteristics and primary crop rotation |
| `experience` | `INTEGER` | Farming experience in years |
| `annual_income` / `monthly_income`| `TEXT` | Income brackets |
| `has_loan` / `loan_amount` | `TEXT` | Crop loan status & outstanding balance |
| **`loan_due_date`** | **`TEXT`** | **Next loan / EMI payment due date (`YYYY-MM-DD`)** |
| `bank_name` | `TEXT` | Primary lending bank |
| `has_kcc` | `TEXT` | Kisan Credit Card cardholder status |
| `existing_emi` | `TEXT` | Monthly EMI burden |
| `has_insurance` | `TEXT` | PMFBY Crop Insurance coverage |
| `farmer_category` | `TEXT` | Marginal / Small / Medium / Large |
| `is_fpo_member` | `TEXT` | Farmer Producer Organization membership |
| `created_at` | `TIMESTAMP` | Account registration timestamp |

---

## 📡 REST API Reference

### 1. Loan Due Tracker Update
- **Endpoint**: `POST /api/loan-tracker/update`
- **Contributor**: Shrim
- **Headers**: `Content-Type: application/json`
- **Payload**:
  ```json
  {
    "dueDate": "2026-10-31"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "success",
    "tracker": {
      "days_left": 15,
      "days_display": "15",
      "formatted_due_date": "31 Oct 2026",
      "label_text": "Days Left",
      "status": "safe",
      "status_badge": "On Track",
      "status_color": "#16a34a",
      "stroke_dashoffset": 157.08,
      "reminder_message": "EMI Reminder will be sent 15 days before due date (31 Oct 2026)"
    }
  }
  ```

### 2. User Authentication
- **Endpoint**: `POST /api/login`
- **Payload**: `{ "email": "ramesh@kisan.in", "password": "password123" }`
- **Response**: Sets secure session and returns user profile JSON.

### 3. Session User Query
- **Endpoint**: `GET /api/user`
- **Response**: Returns active user metadata and authentication status.

---

## 💻 Local Setup & Execution Guide

### Prerequisites
- Python 3.9 or higher installed
- Pip package manager

### 1. Clone or Open Project
```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Flask Server
```bash
python app.py
```
*The server will start at `http://127.0.0.1:5000` with hot-reloading enabled.*

### 4. Test Credentials
- **URL**: `http://127.0.0.1:5000`
- **Email**: `ramesh@kisan.in`
- **Password**: `password123`

---

## 📦 Git Commit Workflow for Team Members

To keep individual teammate contributions clean and separated in the Git commit history:

### Committing the Loan Due Tracker Feature (*Shrim*):
```bash
git add loan_tracker.py templates/register.html templates/home.html static/css/home.css app.py README.md
git commit -m "feat(loan-tracker): implement dynamic loan due tracker with countdown ring and registration integration"
```

---

## 🔮 Upcoming Team Modules
1. **AI Leaf Disease Classification**: CNN / Vision model for uploading leaf photos and diagnosing infections (Rust, Blight, Mildew).
2. **Automated WhatsApp / SMS Gateway**: Dispatching localized weather alerts and EMI reminders via Twilio or Gupshup.
3. **Mandi Real-Time Feed**: Scheduled background scraping of Government APMC market rates.
4. **Soil Health Card Advisor**: Recommendation engine for Urea, DAP, and Potash dosages based on NPK sensor telemetry.
