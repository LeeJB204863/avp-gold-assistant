import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

# ------------------------------------------------
# อ่าน API KEY (ปลอดภัย) — 3 ทางเลือกลำดับความสำคัญ:
# 1) st.secrets["GOLDAPI_KEY"] (แนะนำสำหรับ Streamlit Cloud)
# 2) environment variable (ถ้าตั้งในระบบ)
# 3) None -> จะแจ้ง error ให้ผู้ใช้ใส่ key ใน Secrets
# ------------------------------------------------
def get_api_key():
    # 1) st.secrets (Streamlit Cloud)
    try:
        key = st.secrets["GOLDAPI_KEY"]
        if key:
            return key
    except Exception:
        pass

    # 2) environment variable
    key = os.getenv("GOLDAPI_KEY")
    if key:
        return key

    # 3) ถ้าไม่เจอ ให้ return None
    return None

# ------------------------------------------------
# ฟังก์ชันดึงราคาทองสด (ใช้ GoldAPI)
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
# ฟังก์ชัน Premium / Discount
# ------------------------------------------------
def check_zone(entry, high, low):
    mid = (high + low) / 2
    if entry > mid:
        return "📍 Premium Zone (ควรเน้น Sell)"
    else:
        return "📍 Discount Zone (ควรเน้น Buy)"

# ------------------------------------------------
# Session สำหรับเก็บแผน
# ------------------------------------------------
if "plans" not in st.session_state:
    st.session_state["plans"] = []

# ------------------------------------------------
# UI เริ่มต้น
# ------------------------------------------------
st.title("AVP Gold Assistant V3 (with GoldAPI)")
st.write("✨ เพิ่มราคาทองสด + Mini Chart + Auto Entry")
st.caption("หมายเหตุ: ต้องตั้ง GoldAPI key ใน Streamlit Secrets (ปลอดภัย) หรือ environment variable")

# ------------------------------------------------
# ปุ่มดึงราคาทองสด
# ------------------------------------------------
st.subheader("ราคาทองคำสด (Realtime)")

if st.button("📥 ดึงราคาทองคำตอนนี้"):
    price, err = get_gold_price()
    if err is None and price is not None:
        st.success(f"ราคาล่าสุด: {price:.2f}")
        st.session_state["live_price"] = price
    else:
        # แจ้งข้อความแยกหลายกรณี
        if err == "NO_API_KEY":
            st.error("❗ ไม่พบ GoldAPI key — กรุณาตั้งค่า GoldAPI key ใน Streamlit Secrets (หรือ environment variable GOLDAPI_KEY).")
        elif err == "REQUEST_EXCEPTION":
            st.error("❗ เกิดข้อผิดพลาดขณะเชื่อมต่อ API (network). ลองอีกครั้งหรือเช็คการเชื่อมต่อ.")
        elif err and err.startswith("HTTP_"):
            st.error(f"❗ API ตอบกลับด้วยสถานะ {err}. ลองตรวจสอบ key หรือรออีกสักครู่.")
        else:
            st.error("❗ ไม่สามารถดึงราคาได้ (response ไม่ถูกต้อง).")

live_price = st.session_state.get("live_price", None)

if live_price:
    st.write(f"ราคาล่าสุดที่ดึงมา: **{live_price:.2f}**")

# ------------------------------------------------
# Mini Chart (กราฟราคาย่อ)
# ------------------------------------------------
st.subheader("📉 Mini Chart (10 จุดล่าสุด)")

if live_price:
    # สร้างข้อมูลจำลอง 10 จุด (เพราะ API ฟรีไม่มี historical)
    df = pd.DataFrame({
        "index": list(range(10)),
        "price": [live_price - i*0.8 for i in range(10)][::-1]
    })
    fig = px.line(df, x="index", y="price", title="", markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ดึงราคาทองก่อนเพื่อดูกราฟ")

# ------------------------------------------------
# เลือก Zone
# ------------------------------------------------
st.subheader("1) เลือก Zone ตามระบบ AVP")
zone = st.selectbox(
    "เลือก Zone",
    [
        "Buy Zone A", "Buy Zone B", "Buy Zone C",
        "Sell Zone A", "Sell Zone B", "Sell Zone C",
    ]
)

# ------------------------------------------------
# High / Low ของโซน
# ------------------------------------------------
st.subheader("2) กรอกราคา High / Low ของโซน")
high = st.number_input("High ของโซน", value=4205.00, format="%.2f")
low = st.number_input("Low ของโซน", value=4185.00, format="%.2f")

# ------------------------------------------------
# Entry / SL / TP
# ------------------------------------------------
st.subheader("3) จุดเข้าไม้")

entry = st.number_input(
    "Entry",
    value=live_price if live_price else 4195.00,
    format="%.2f"
)

sl = st.number_input("Stop Loss (SL)", value=4183.55, format="%.2f")
tp = st.number_input("Take Profit (TP)", value=4213.45, format="%.2f")

# ------------------------------------------------
# คำนวณผลลัพธ์
# ------------------------------------------------
rr = calc_rr(entry, sl, tp)
risk = abs(entry - sl)
reward = abs(tp - entry)
zone_status = check_zone(entry, high, low)

# ------------------------------------------------
# สรุปผล
# ------------------------------------------------
st.subheader("📊 สรุปผลการประเมิน")
st.write(f"• Risk: {risk:.2f}")
st.write(f"• Reward: {reward:.2f}")
st.write(f"• RR: **{rr:.2f} R**")
st.write(zone_status)

if rr >= 3:
    st.success("✔ RR ดีมาก เหมาะกับการเข้าไม้ตามระบบ AVP")
elif rr >= 2:
    st.info("⚠ RR ปานกลาง ใช้ได้")
else:
    st.error("✘ RR ต่ำ ไม่ควรเข้าไม้")

# ------------------------------------------------
# ปุ่มบันทึกแผน
# ------------------------------------------------
if st.button("💾 บันทึกแผนเข้าไม้"):
    plan = {
        "zone": zone,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "status": zone_status
    }
    st.session_state["plans"].append(plan)
    st.success("บันทึกแผนเรียบร้อย ✔")

# ------------------------------------------------
# แสดงแผนทั้งหมด
# ------------------------------------------------
st.subheader("📝 แผนที่บันทึกไว้")
if len(st.session_state["plans"]) == 0:
    st.write("ยังไม่มีแผน")
else:
    for i, p in enumerate(st.session_state["plans"]):
        st.write(f"### แผน {i+1}")
        st.write(f"- Zone: {p['zone']}")
        st.write(f"- Entry: {p['entry']}")
        st.write(f"- SL: {p['sl']}")
        st.write(f"- TP: {p['tp']}")
        st.write(f"- RR: {p['rr']:.2f} R")
        st.write(f"- สถานะโซน: {p['status']}")
        st.write("---")


