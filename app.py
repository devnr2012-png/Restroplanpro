import streamlit as st
import pandas as pd
import plotly.express as px
import io
import urllib.parse
import os
import sqlite3
import hashlib
import random
import requests

st.set_page_config(
    page_title="RestoPlan Pro",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FAST2SMS API KEY INTEGRATED ---
FAST2SMS_KEY = "Rg7N51LZuhDCFWsMEorwmBHdpGSye802XnlVP3qU9azA4v6JkY9Eun8zWR4VZq1pdCaeAJUmB27QNFXM"

def send_sms_otp(mobile_num, otp_val):
    clean_num = ""
    for ch in str(mobile_num):
        if ch.isdigit():
            clean_num += ch
    if len(clean_num) == 12 and clean_num.startswith("91"):
        clean_num = clean_num[2:]
    if len(clean_num) != 10:
        return False, "10-digit mobile number required"

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
        res = requests.post(url, data=payload, headers=headers, timeout=8)
        data = res.json()
        if data.get("return") is True:
            return True, "SMS sent to mobile successfully!"
        return False, "SMS Gateway status: " + str(data)
    except Exception as e:
        return False, str(e)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "username TEXT, "
        "identifier TEXT UNIQUE, "
        "password TEXT, "
        "mega_plan INTEGER DEFAULT 0)"
    )
    try:
        c.execute("ALTER TABLE users ADD COLUMN mega_plan INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    c.execute(
        "CREATE TABLE IF NOT EXISTS otps ("
        "identifier TEXT PRIMARY KEY, "
        "otp TEXT)"
    )
    conn.commit()
    conn.close()

init_db()

def hash_pw(pw_text):
    return hashlib.sha256(pw_text.encode()).hexdigest()

# 2. Session States
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "is_paid" not in st.session_state:
    st.session_state["is_paid"] = False
if "mega_plan_active" not in st.session_state:
    st.session_state["mega_plan_active"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "identifier" not in st.session_state:
    st.session_state["identifier"] = ""
if "otp_sent" not in st.session_state:
    st.session_state["otp_sent"] = False
if "otp_verified" not in st.session_state:
    st.session_state["otp_verified"] = False
if "fp_target" not in st.session_state:
    st.session_state["fp_target"] = ""
if "curr_otp" not in st.session_state:
    st.session_state["curr_otp"] = ""
if "sms_status" not in st.session_state:
    st.session_state["sms_status"] = ""

# 3. Clean CSS
css_str = (
    "<style>"
    "[data-testid='stAppViewContainer'] { background-color: #F8FAFC !important; }"
    "[data-testid='stHeader'] { background-color: #FFFFFF !important; }"
    ".title-text { font-size: 36px; font-weight: 800; color: #0F172A; text-align: center; }"
    ".subtitle-text { font-size: 14px; color: #B45309; text-align: center; font-weight: 700; margin-bottom: 20px; }"
    ".stButton > button { background-color: #000000 !important; color: #FFFFFF !important; font-weight: 700 !important; border-radius: 8px !important; }"
    ".stButton > button p, .stButton > button span { color: #FFFFFF !important; }"
    ".locked-box { text-align: center; padding: 20px; background-color: #FFFBEB; border-radius: 10px; border: 2px dashed #D97706; margin-bottom: 15px; }"
    "</style>"
)
st.markdown(css_str, unsafe_allow_html=True)

st.markdown('<div class="title-text">🍽️ RestoPlan Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">RESTAURANT STARTUP BUDGET & ROI ANALYZER</div>', unsafe_allow_html=True)

# 4. Auth System
if not st.session_state["logged_in"]:
    col_l, col_r = st.columns([1.2, 1], gap="large")
    with col_l:
        st.markdown("### 🌟 Plan Your Food Startup")
        st.write("Professional budget calculator for Cloud Kitchens, Cafes, and Fine Dining.")
        i1, i2 = st.columns(2)
        with i1:
            st.image("https://images.unsplash.com/photo-1556910103-1c02745aae4d?q=80&w=400", caption="Cloud Kitchen", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=400", caption="Cafe & Bakery", use_container_width=True)
        with i2:
            st.image("https://images.unsplash.com/photo-1552566626-52f8b828add9?q=80&w=400", caption="Fine Dining", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1565299585323-38d6b0865b47?q=80&w=400", caption="QSR Truck", use_container_width=True)

    with col_r.container(border=True):
        st.markdown("### 🔐 Account Portal")
        auth_mode = st.radio("Choose Action", ["Login", "Register", "Forgot Password"], horizontal=True)

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        if "Login" in auth_mode:
            st.info("Log in with your Mobile/Email and Password.")
            log_id = st.text_input("Mobile Number or Email", key="log_id_in")
            log_pw = st.text_input("Password", type="password", key="log_pw_in")

            if st.button("Login", use_container_width=True, key="btn_login_sub"):
                if log_id and log_pw:
                    hp = hash_pw(log_pw)
                    c.execute(
                        "SELECT username, mega_plan FROM users WHERE identifier = ? AND password = ?",
                        (log_id.strip(), hp)
                    )
                    res = c.fetchone()
                    if res:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = res[0]
                        st.session_state["identifier"] = log_id.strip()
                        st.session_state["mega_plan_active"] = bool(res[1])
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    st.error("Please enter details.")

        elif "Register" in auth_mode:
            st.info("Create a new RestoPlan account.")
            r_name = st.text_input("Full Name", key="r_name_in")
            r_id = st.text_input("10-Digit Mobile or Email", key="r_id_in")
            r_pw = st.text_input("Password", type="password", key="r_pw_in")

            if st.button("Register Now", use_container_width=True, key="btn_reg_sub"):
                if r_name and r_id and r_pw:
                    c.execute("SELECT username FROM users WHERE identifier = ?", (r_id.strip(),))
                    if c.fetchone():
                        st.error("Account already exists with this ID! Please login.")
                    else:
                        hp = hash_pw(r_pw)
                        c.execute(
                            "INSERT INTO users (username, identifier, password, mega_plan) VALUES (?, ?, ?, 0)",
                            (r_name.strip(), r_id.strip(), hp)
                        )
                        conn.commit()
                        st.success("Registration Successful! Now switch to Login tab.")
                else:
                    st.error("All fields are required.")

        elif "Forgot" in auth_mode:
            st.info("Reset your password using Mobile OTP.")

            # Step 1: Send OTP
            if not st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                fp_phone = st.text_input("10-Digit Registered Mobile", key="fp_phone_in")
                if st.button("Send SMS OTP", use_container_width=True, key="btn_send_otp"):
                    if fp_phone:
                        target = fp_phone.strip()
                        c.execute("SELECT username FROM users WHERE identifier = ?", (target,))
                        found = c.fetchone()
                        if found:
                            code = str(random.randint(1000, 9999))
                            c.execute(
                                "INSERT OR REPLACE INTO otps (identifier, otp) VALUES (?, ?)",
                                (target, code)
                            )
                            conn.commit()
                            ok, stat = send_sms_otp(target, code)
                            st.session_state["otp_sent"] = True
                            st.session_state["fp_target"] = target
                            st.session_state["curr_otp"] = code
                            st.session_state["sms_status"] = stat
                            st.rerun()
                        else:
                            st.error("Mobile number is not registered. Please Register first.")
                    else:
                        st.error("Please enter mobile number.")

            # Step 2: Verify OTP
            elif st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                st.write(f"OTP sent to: **{st.session_state['fp_target']}**")
                if "success" in st.session_state.get("sms_status", "").lower():
                    st.success(f"📲 {st.session_state['sms_status']}")
                else:
                    st.warning(f"Gateway Notice: {st.session_state.get('sms_status', '')}")
                    st.info(f"Screen Backup OTP: **{st.session_state.get('curr_otp', '')}**")

                otp_in = st.text_input("Enter 4-Digit OTP", key="otp_in_field")
                v_col1, v_col2 = st.columns(2)
                with v_col1:
                    if st.button("Verify OTP", use_container_width=True, key="btn_verify_otp"):
                        c.execute("SELECT otp FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                        db_otp = c.fetchone()
                        if db_otp and db_otp[0] == otp_in.strip():
                            st.session_state["otp_verified"] = True
                            st.success("OTP
