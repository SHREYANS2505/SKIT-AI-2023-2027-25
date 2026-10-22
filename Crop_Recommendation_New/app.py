"""Small Streamlit interface for the alternative crop recommendation model."""
import streamlit as st
from src.recommend import recommend
from src.data_validation import validate_sample

st.set_page_config(page_title="CropWise Alternative", page_icon="🌱", layout="centered")
st.title("🌱 CropWise — Alternative Crop Recommendation")
st.caption("A separate dataset and model pipeline for educational experimentation.")
with st.form("crop_form"):
    c1, c2 = st.columns(2)
    with c1:
        nitrogen = st.number_input("Nitrogen (N)", 0.0, 140.0, 55.0)
        phosphorus = st.number_input("Phosphorus (P)", 0.0, 145.0, 45.0)
        potassium = st.number_input("Potassium (K)", 0.0, 210.0, 40.0)
        temperature = st.number_input("Temperature °C", -5.0, 55.0, 26.0)
    with c2:
        humidity = st.number_input("Humidity %", 0.0, 100.0, 65.0)
        ph = st.number_input("Soil pH", 3.0, 10.0, 6.5)
        rainfall = st.number_input("Rainfall (mm)", 0.0, 400.0, 70.0)
        soil_type = st.selectbox("Soil type", ["loamy", "clayey", "sandy", "silty"])
    season = st.selectbox("Season", ["kharif", "rabi", "zaid"])
    region_zone = st.selectbox("Region climate zone", ["arid", "semi_arid", "sub_humid", "humid"])
    submitted = st.form_submit_button("Recommend crops")
if submitted:
    sample = locals().copy()
    sample = {key: sample[key] for key in ["nitrogen","phosphorus","potassium","temperature","humidity","ph","rainfall","soil_type","season","region_zone"]}
    try:
        results = recommend(sample, top_k=5)
        st.subheader("Top candidates")
        for item in results:
            st.write(f"**{item['crop'].replace('_',' ').title()}** — {item['probability']:.1%}")
            st.progress(min(1.0, item["probability"]))
        st.info("Use local soil tests and extension-service guidance before making planting decisions.")
    except Exception as exc:
        st.error(str(exc))
