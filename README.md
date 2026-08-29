# Last Update


https://github.com/user-attachments/assets/3fb9daa1-7362-435e-b4b9-f2660a531338


<img width="1854" height="938" alt="image" src="https://github.com/user-attachments/assets/fd35febe-9117-470b-8041-608ea85b2d93" />

<img width="1851" height="947" alt="image" src="https://github.com/user-attachments/assets/b24479d7-0f23-4e5f-aabd-35ae42cbfa70" />



# KisaanRaksha 🌾

**KisaanRaksha** is an AI-powered platform to help Indian farmers with:
- 📊 Crop risk assessment
- 💰 Market (mandi) price forecasting
- 🌱 Crop recommendations
- 🏛️ Government scheme discovery
- 🌦️ Weather alerts

## Project Structure
```
kisaanraksha/
├── frontend/       # HTML, CSS, JS UI
├── backend/         # Python backend (Flask/FastAPI)
│   ├── models/      # ML model definitions
│   ├── services/    # External API integrations
│   ├── data/        # Static datasets
│   └── trained_models/  # Serialised .pkl / .h5 files
├── notebooks/       # Jupyter training notebooks
├── requirements.txt
└── .env             # Environment variables (never commit!)
```

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
python backend/app.py

