import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ------------------------------------------------
# ฟังก์ชันดึงราคาทองจาก GoldAPI.io
# ------------------------------------------------
def get_gold_price():
    try:
        api_key = st.secrets["GOLDAPI_KEY"]

        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {
            "x-access-token": api_key,
            "Content-Type": "application/json"
        }

        r = requests.get(url, headers=headers)
        data = r.json()

        return data.get("price", None)

    except Exception as e:
        return None


# ------------------------------------------------
# ฟังก์ชันคำนวณ RR
# ------------------------------------------------
def calc_rr(entry, sl, tp):
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk == 0:
        return 0
    return reward / risk


# ------------------------------------------------
# ฟังก์ชัน Premium / Discount Zone
# ------------------------------------------------
def check_zone(entry, high, low):
    mid = (high + low) / 2
    if entry > mid:
        return "📍 Premium Zone (แนวโน้มเทขาย)"
    else:
        return "📍 Discount Zone (แนวโน้มเข้าซื้อ)"


# ------------------------------------------------
# Session สำหรับเก็บแผน
# ------------------------------------------------
if "plans" not in st.session_state:
    st.session_state["plans"] = []


# ------------------------------------------------
# UI เริ่มต้น
# ------------------------------------------------
st.title("AVP Gold Assistant V3")
st.write("✨ Assistant สำหรับเทรดทองคำตามระบบ AVP (เวอร์ชันมือถือ/เว็บ)")


# ------------------------------------------------
# ราคาทองคำสด
# ------------------------------------------------
st.subheader("ราคาทองคำ Realtime")

if st.button("📥 ดึงราคาทองคำตอนนี้"):
    price = get_gold_price()
    if price:
        st.session_state["live_price"] = price
        st.success(f"ราคาล่าสุด: {price:.2f} USD")
    else:
        st.error("❗ ดึงราคาทองคำไม่สำเร็จ (API Error)")


live_price = st.session_state.get("live_price", None)

if live_price:
    st.write(f"ราคาทองคำล่าสุด: **{live_price:.2f} USD**")


# --------------------


