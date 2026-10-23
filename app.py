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

# 1. Page Configuration
st.set_page_config(page_title="RestoPlan Pro", page_icon="🍽️", layout="wide", initial_sidebar_state="expanded")

# --- FAST2SMS API CONFIGURATION ---
FAST2SMS_API_KEY = "Rg7N51LZuhDCFWsMEorwmBHdpGSye802XnlVP3qU9azA4v6JkY9Eun8zWR4VZq1pdCaeAJUmB27QNFXM"

def send_sms_otp(mobile_number, otp_code):
    clean_mobile = "".join(filter(str.isdigit, str(mobile_number)))
    if len(clean_mobile) == 12 and clean_mobile.startswith("91"):
        clean_mobile = clean_mobile[2:]
    
    if len(clean_mobile) != 10:
        return False, "Kripya valid 10-digit mobile number dalein."

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "message": f"Your RestoPlan Pro OTP is {otp_code}. Do not share this OTP.",
        "language": "english",
        "route": "q",
        "numbers": clean_mobile
    }
    headers = {
        'authorization': FAST2SMS_API_KEY.strip(),
        'Content-Type': "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get("return") is True:
            return True, "SMS aapke mobile par successfully send ho gaya!"
        else:
            msg = res_json.get("message", "API Route Error")
            if isinstance(msg, list) and len(msg) > 0:
                msg = msg[0]
            return False, f"{msg}"
    except Exception as e:
        return False, f"Network issue: {str(e)}"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, identifier TEXT UNIQUE, password TEXT, mega_plan INTEGER DEFAULT 0)')
    try:
        c.execute('ALTER TABLE users ADD COLUMN mega_plan INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    c.execute('CREATE TABLE IF NOT EXISTS otps (identifier TEXT PRIMARY KEY, otp TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. Session State Initialization
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
if "current_otp" not in st.session_state:
    st.session_state["current_otp"] = ""
if "sms_status_msg" not in st.session_state:
    st.session_state["sms_status_msg"] = ""

# 3. Clean White Background & Crisp Button CSS
css_rules = (
    "<style>"
    "[data-testid='stAppViewContainer'] { background-color: #F8FAFC !important; }"
    "[data-testid='stHeader'] { background-color: #FFFFFF !important; border-bottom: 1px solid #E2E8F0; }"
    ".title-text { font-size: 38px; font-weight: 800; color: #0F172A !important; text-align: center; margin-top: 5px; margin-bottom: 0px; }"
    ".subtitle-text { font-size: 15px; color: #B45309 !important; text-align: center; margin-bottom: 25px; font-weight: 700; letter-spacing: 1.2px; }"
    ".stButton > button, button[kind='primary'], button[kind='secondary'] { background-color: #000000 !important; color: #FFFFFF !important; border: 1px solid #000000 !important; border-radius: 8px !important; font-size: 16px !important; font-weight: 700 !important; padding: 10px 20px !important; }"
    ".stButton > button p, .stButton > button span, .stButton > button div { color: #FFFFFF !important; font-weight: 700 !important; }"
    ".stButton > button:hover, .stButton > button:hover p, .stButton > button:hover span { background-color: #262626 !important; color: #FBBF24 !important; border-color: #262626 !important; }"
    ".locked-section { text-align: center; padding: 25px; background-color: #FFFBEB !important; border-radius: 12px; border: 2px dashed #D97706 !important; margin-bottom: 20px; }"
    "</style>"
)
st.markdown(css_rules, unsafe_allow_html=True)

# Logo & Header
col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown('<div style="text-align: center; font-size: 42px;">🍽️</div>', unsafe_allow_html=True)
    st.markdown('<div class="title-text">RestoPlan Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">ULTIMATE RESTAURANT STARTUP BUDGET & ROI ANALYZER</div>', unsafe_allow_html=True)

# 4. Auth System
if not st.session_state["logged_in"]:
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.markdown("<h3 style='color: #0F172A; margin-top: 0px;'>🌟 Plan Your Dream Food Business</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #475569; font-size: 15px;'>Easily budget, discover top local vendors, and analyze profitability for Cloud Kitchens, Fine Dining Restaurants, Cozy Cafes, and QSR / Food Trucks.</p>", unsafe_allow_html=True)
        ig1, ig2 = st.columns(2)
        with ig1:
            st.image("https://images.unsplash.com/photo-1556910103-1c02745aae4d?q=80&w=500&auto=format&fit=crop", caption="Cloud Kitchen Setup", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=500&auto=format&fit=crop", caption="Cozy Cafe & Bakery", use_container_width=True)
        with ig2:
            st.image("https://images.unsplash.com/photo-1552566626-52f8b828add9?q=80&w=500&auto=format&fit=crop", caption="Fine Dining Restaurant", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1565299585323-38d6b0865b47?q=80&w=500&auto=format&fit=crop", caption="QSR & Food Truck", use_container_width=True)
            
    with col_right.container(border=True):
        st.markdown("<h3 style='color: #0F172A; margin-top: 0px;'>🔐 Secure Account Portal</h3>", unsafe_allow_html=True)
        auth_action = st.radio("Select Action", ["Login", "Register", "Forgot Password"], horizontal=True, key="auth_action_radio")
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        if "Login" in auth_action:
            st.info("Log in with your registered Mobile Number/Email and Password.")
            log_identifier = st.text_input("Mobile Number or Email", key="login_id_field")
            log_pass = st.text_input("Password", type="password", key="login_pass_field")
            
            if st.button("Login", use_container_width=True, key="login_submit_btn"):
                if log_identifier and log_pass:
                    hashed_pw = hash_password(log_pass)
                    c.execute("SELECT username, mega_plan FROM users WHERE identifier = ? AND password = ?", (log_identifier, hashed_pw))
                    user = c.fetchone()
                    if user:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = user[0]
                        st.session_state["identifier"] = log_identifier
                        st.session_state["mega_plan_active"] = bool(user[1])
                        st.rerun()
                    else:
                        st.error("❌ Invalid Mobile/Email or Password.")
                else:
                    st.error("Please enter both Mobile/Email and Password.")
                    
        elif "Register" in auth_action:
            st.info("Create your account using your Name, Mobile/Email and Password.")
            reg_name = st.text_input("Full Name", key="register_name_field")
            reg_identifier = st.text_input("Mobile Number or Email", key="register_id_field")
            reg_pass = st.text_input("Password", type="password", key="register_pass_field")
            
            if st.button("Register Now", use_container_width=True, key="register_submit_btn"):
                if reg_name and reg_identifier and reg_pass:
                    c.execute("SELECT * FROM users WHERE identifier = ?", (reg_identifier,))
                    if c.fetchone():
                        st.error("⚠️ An account with this Mobile/Email already exists! Please login.")
                    else:
                        hashed_pw = hash_password(reg_pass)
                        c.execute("INSERT INTO users (username, identifier, password, mega_plan) VALUES (?, ?, ?, 0)", (reg_name, reg_identifier, hashed_pw))
                        conn.commit()
                        st.success("✅ Registration Successful! Please switch to Login tab.")
                else:
                    st.error("Please fill in all details.")
                    
        elif "Forgot" in auth_action:
            st.info("Reset your password using an SMS OTP sent directly to your Mobile Phone.")
            
            # Step 1: Request OTP
            if not st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                fp_identifier = st.text_input("Registered 10-digit Mobile Number", key="fp_id_field")
                if st.button("Send SMS OTP", use_container_width=True, key="send_otp_btn"):
                    if fp_identifier:
                        c.execute("SELECT username FROM users WHERE identifier = ?", (fp_identifier,))
                        user = c.fetchone()
                        if user:
                            otp_val = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO otps (identifier, otp) VALUES (?, ?)", (fp_identifier, otp_val))
                            conn.commit()
                            
                            ok, status_txt = send_sms_otp(fp_identifier, otp_val)
                            st.session_state["otp_sent"] = True
                            st.session_state["fp_target"] = fp_identifier
                            st.session_state["current_otp"] = otp_val
                            st.session_state["sms_status_msg"] = status_txt
                            st.rerun()
                        else:
                            st.error("❌ Yeh Mobile Number registered nahi hai. Pehle Register karein.")
                    else:
                        st.error("Kripya apna registered 10-digit Mobile Number dalein.")

            # Step 2: Enter & Verify OTP
            elif st.session_state["otp_sent"] and not st.session_state["otp_verified"]:
                st.write(f"OTP request mobile: **{st.session_state.get('fp_target', '')}**")
                
                if "successfully" in st.session_state.get("sms_status_msg", "").lower():
                    st.success(f"📲 {st.session_state['sms_status_msg']}")
                else:
                    st.warning(f"Gateway Notice: {st.session_state.get('sms_status_msg', '')}")
                    st.info(f"Screen Alert (Instant OTP): **{st.session_state.get('current_otp', '')}**")
                
                entered_otp = st.text_input("Enter 4-digit OTP", key="entered_otp_field")
                
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    if st.button("Verify OTP", use_container_width=True, key="verify_otp_btn"):
                        c.execute("SELECT otp FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                        row = c.fetchone()
                        if row and row[0] == entered_otp:
                            st.session_state["otp_verified"] = True
                            st.success("✅ OTP Verified! Ab naya password set karein.")
                            st.rerun()
                        else:
                            st.error("❌ Galat OTP. Dobara check karke enter karein.")
                with col_v2:
                    if st.button("Resend OTP", use_container_width=True, key="resend_fp_btn"):
                        st.session_state["otp_sent"] = False
                        st.session_state["otp_verified"] = False
                        st.rerun()

            # Step 3: Set New & Confirm Password
            elif st.session_state["otp_verified"]:
                st.success(f"Verified User: **{st.session_state.get('fp_target', '')}**")
                new_pass = st.text_input("New Password", type="password", key="new_pass_field")
                confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass_field")
                
                if st.button("Reset & Save Password", use_container_width=True, key="save_pass_btn"):
                    if not new_pass or not confirm_pass:
                        st.error("Dono password fields bharein.")
                    elif new_pass != confirm_pass:
                        st.error("❌ Passwords match nahi ho rahe hain.")
                    else:
                        hashed_new = hash_password(new_pass)
                        c.execute("UPDATE users SET password = ? WHERE identifier = ?", (hashed_new, st.session_state["fp_target"]))
                        c.execute("DELETE FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                        conn.commit()
                        st.session_state["otp_sent"] = False
                        st.session_state["otp_verified"] = False
                        st.session_state["fp_target"] = ""
                        st.success("🎉 Password reset ho gaya! Ab Login tab par jaakar login karein.")
                        
        conn.close()
    st.stop()

# --- APP DASHBOARD (AFTER LOGIN) ---
st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state['username']}**")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.session_state["is_paid"] = False
    st.session_state["mega_plan_active"] = False
    st.session_state["username"] = ""
    st.session_state["identifier"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Setup Details")
country = st.sidebar.selectbox("Select Country", ["India", "USA", "UAE", "UK", "Australia"])
location_type = st.sidebar.selectbox("Location Type", ["Metro City", "Tier 2 City", "Tier 3 City", "Highway"])
currency = st.sidebar.selectbox("Select Currency", ["₹ (INR)", "$ (USD)"])
restaurant_type = st.sidebar.selectbox("Restaurant Model", ["Cloud Kitchen", "Fine Dining", "QSR", "Cafe", "Food Truck"])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛠️ 1. Setup Costs", 
    "🔄 2. Monthly Costs", 
    "📊 3. Pro Analytics & ROI", 
    "📥 4. Export Plan", 
    "📍 5. Location & Top 5 Vendors",
    "🔥 6. Step-by-Step Walkthrough"
])

with tab1:
    st.subheader(f"Initial Setup Investment for {restaurant_type} ({location_type}, {country})")
    col1, col2 = st.columns(2)
    with col1:
        deposit = st.number_input(f"Security Deposit ({currency})", value=200000, step=10000)
        interior = st.number_input(f"Furniture & Decor ({currency})", value=300000, step=10000)
    with col2:
        kitchen_eq = st.number_input(f"Kitchen Equipment ({currency})", value=400000, step=20000)
        licenses = st.number_input(f"Licenses & POS ({currency})", value=45000, step=1000)
    total_capex = deposit + interior + kitchen_eq + licenses
    st.info(f"**Total Capital Expenditure:** {currency} {total_capex:,.2f}")

with tab2:
    st.subheader("Monthly Running Expenses")
    col3, col4 = st.columns(2)
    with col3:
        rent = st.number_input(f"Monthly Rent ({currency})", value=50000, step=5000)
        staffing = st.number_input(f"Staff Salary ({currency})", value=80000, step=5000)
    with col4:
        raw_materials = st.number_input(f"Raw Materials ({currency})", value=100000, step=5000)
        utilities = st.number_input(f"Utilities & Marketing ({currency})", value=30000, step=100
