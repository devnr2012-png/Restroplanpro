import streamlit as st
import pandas as pd
import plotly.express as px
import io
import urllib.parse
import sqlite3
import hashlib
import random
import requests

st.set_page_config(page_title="RestoPlan Pro", page_icon="🍽️", layout="wide")

FAST2SMS_KEY = "Rg7N51LZuhDCFWsMEorwmBHdpGSye802XnlVP3qU9azA4v6JkY9Eun8zWR4VZq1pdCaeAJUmB27QNFXM"

def send_sms_otp(mobile_num, otp_val):
    clean_num = "".join([c for c in str(mobile_num) if c.isdigit()])
    if len(clean_num) == 12 and clean_num.startswith("91"):
        clean_num = clean_num[2:]
    if len(clean_num) != 10:
        return False, "10-digit mobile required"

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "message": f"RestoPlan Pro OTP: {otp_val}",
        "language": "english",
        "route": "q",
        "numbers": clean_num
    }
    headers = {
        "authorization": FAST2SMS_KEY.strip(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=8)
        data = r.json()
        if data.get("return") is True:
            return True, "SMS sent successfully!"
        return False, str(data.get("message", "Gateway error"))
    except Exception as e:
        return False, str(e)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, identifier TEXT UNIQUE, password TEXT, mega_plan INTEGER DEFAULT 0)")
    try:
        c.execute("ALTER TABLE users ADD COLUMN mega_plan INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    c.execute("CREATE TABLE IF NOT EXISTS otps (identifier TEXT PRIMARY KEY, otp TEXT)")
    conn.commit()
    conn.close()

init_db()

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

for k, v in [
    ("logged_in", False), ("is_paid", False), ("mega_plan_active", False),
    ("username", ""), ("identifier", ""), ("otp_sent", False),
    ("otp_verified", False), ("fp_target", ""), ("curr_otp", ""), ("sms_msg", "")
]:
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown("""
<style>
[data-testid='stAppViewContainer'] { background-color: #F8FAFC !important; }
[data-testid='stHeader'] { background-color: #FFFFFF !important; }
.title-text { font-size: 34px; font-weight: 800; color: #0F172A; text-align: center; }
.subtitle-text { font-size: 14px; color: #B45309; text-align: center; font-weight: 700; margin-bottom: 20px; }
.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; font-weight: 700 !important; border-radius: 8px !important; }
.stButton > button p, .stButton > button span { color: #FFFFFF !important; }
.locked-box { text-align: center; padding: 20px; background-color: #FFFBEB; border-radius: 10px; border: 2px dashed #D97706; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-text">🍽️ RestoPlan Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">RESTAURANT STARTUP BUDGET & ROI ANALYZER</div>', unsafe_allow_html=True)

if not st.session_state["logged_in"]:
    col_l, col_r = st.columns([1.2, 1], gap="large")
    with col_l:
        st.markdown("### 🌟 Plan Your Food Startup")
        st.write("Professional budgeting for Cloud Kitchens, Cafes, and Fine Dining.")
        i1, i2 = st.columns(2)
        with i1:
            st.image("https://images.unsplash.com/photo-1556910103-1c02745aae4d?q=80&w=400", caption="Cloud Kitchen", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=400", caption="Cafe", use_container_width=True)
        with i2:
            st.image("https://images.unsplash.com/photo-1552566626-52f8b828add9?q=80&w=400", caption="Fine Dining", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1565299585323-38d6b0865b47?q=80&w=400", caption="QSR Truck", use_container_width=True)

    with col_r.container(border=True):
        st.markdown("### 🔐 Account Portal")
        mode = st.radio("Choose", ["Login", "Register", "Forgot Password"], horizontal=True)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        if mode == "Login":
            log_id = st.text_input("Mobile or Email", key="lid")
            log_pw = st.text_input("Password", type="password", key="lpw")
            if st.button("Login", use_container_width=True):
                if log_id and log_pw:
                    c.execute("SELECT username, mega_plan FROM users WHERE identifier = ? AND password = ?", (log_id.strip(), hash_pw(log_pw)))
                    row = c.fetchone()
                    if row:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = row[0]
                        st.session_state["identifier"] = log_id.strip()
                        st.session_state["mega_plan_active"] = bool(row[1])
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

        elif mode == "Register":
            r_name = st.text_input("Full Name", key="rnm")
            r_id = st.text_input("10-Digit Mobile or Email", key="rid")
            r_pw = st.text_input("Password", type="password", key="rpw")
            if st.button("Register Now", use_container_width=True):
                if r_name and r_id and r_pw:
                    c.execute("SELECT username FROM users WHERE identifier = ?", (r_id.strip(),))
                    if c.fetchone():
                        st.error("Account exists. Please login.")
                    else:
                        c.execute("INSERT INTO users VALUES (?, ?, ?, 0)", (r_name.strip(), r_id.strip(), hash_pw(r_pw), 0))
                        conn.commit()
                        st.success("Registered! Switch to Login tab.")

        elif mode == "Forgot Password":
            if not st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                f_phone = st.text_input("10-Digit Mobile", key="fph")
                if st.button("Send SMS OTP", use_container_width=True):
                    if f_phone:
                        target = f_phone.strip()
                        c.execute("SELECT username FROM users WHERE identifier = ?", (target,))
                        if c.fetchone():
                            code = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO otps VALUES (?, ?)", (target, code))
                            conn.commit()
                            ok, stat = send_sms_otp(target, code)
                            st.session_state["otp_sent"] = True
                            st.session_state["fp_target"] = target
                            st.session_state["curr_otp"] = code
                            st.session_state["sms_msg"] = stat
                            st.rerun()
                        else:
                            st.error("Mobile not registered.")

            elif st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                st.write(f"Target: **{st.session_state['fp_target']}**")
                if "success" in st.session_state.get("sms_msg", "").lower():
                    st.success("📲 SMS dispatched to mobile!")
                else:
                    st.warning(f"SMS: {st.session_state.get('sms_msg', '')}")
                    st.info(f"Screen Backup OTP: **{st.session_state.get('curr_otp', '')}**")

                o_in = st.text_input("Enter 4-Digit OTP", key="oin")
                v1, v2 = st.columns(2)
                with v1:
                    if st.button("Verify OTP", use_container_width=True):
                        c.execute("SELECT otp FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                        db_o = c.fetchone()
                        if db_o and db_o[0] == o_in.strip():
                            st.session_state["otp_verified"] = True
                            st.rerun()
                        else:
                            st.error("Invalid OTP.")
                with v2:
                    if st.button("Resend", use_container_width=True):
                        st.session_state["otp_sent"] = False
