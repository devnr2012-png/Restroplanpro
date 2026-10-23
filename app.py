import streamlit as st
import pandas as pd
import plotly.express as px
import io
import urllib.parse
import os
import sqlite3
import hashlib
import random

# 1. Page Configuration
st.set_page_config(page_title="RestoPlan Pro", page_icon="🍽️", layout="wide", initial_sidebar_state="expanded")

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

# 3. Clean White Background & Crisp Button CSS
css_rules = """
<style>
[data-testid='stAppViewContainer'] {
    background-color: #F8FAFC !important;
}
[data-testid='stHeader'] {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0;
}
.title-text { 
    font-size: 38px; 
    font-weight: 800; 
    color: #0F172A !important; 
    text-align: center; 
    margin-top: 5px; 
    margin-bottom: 0px; 
}
.subtitle-text { 
    font-size: 15px; 
    color: #B45309 !important; 
    text-align: center; 
    margin-bottom: 25px; 
    font-weight: 700; 
    letter-spacing: 1.2px; 
}
.stButton > button, 
button[kind="primary"], 
button[kind="secondary"] {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    border: 1px solid #000000 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
}
.stButton > button p, 
.stButton > button span, 
.stButton > button div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
.stButton > button:hover, 
.stButton > button:hover p, 
.stButton > button:hover span {
    background-color: #262626 !important;
    color: #FBBF24 !important;
    border-color: #262626 !important;
}
.locked-section { 
    text-align: center; 
    padding: 25px; 
    background-color: #FFFBEB !important; 
    border-radius: 12px; 
    border: 2px dashed #D97706 !important; 
    margin-bottom: 20px; 
}
.mega-banner { 
    background: linear-gradient(135deg, #1E293B, #0F172A) !important; 
    border: 2px solid #D97706; 
    border-radius: 14px; 
    padding: 22px; 
    color: #F8FAFC !important; 
    text-align: center; 
    margin-bottom: 20px; 
}
.mega-banner h2, .mega-banner p, .mega-banner b { color: #FFFFFF !important; }
</style>
"""
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

# 4. Auth System (Login, Register, Forgot Password)
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
            st.info("Reset your password using an OTP sent to your Mobile/Email.")
            fp_identifier = st.text_input("Registered Mobile Number or Email", key="fp_id_field")
            
            if not st.session_state["otp_sent"]:
                if st.button("Send OTP", use_container_width=True, key="send_otp_btn"):
                    if fp_identifier:
                        c.execute("SELECT username FROM users WHERE identifier = ?", (fp_identifier,))
                        user = c.fetchone()
                        if user:
                            otp_val = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO otps (identifier, otp) VALUES (?, ?)", (fp_identifier, otp_val))
                            conn.commit()
                            st.session_state["otp_sent"] = True
                            st.session_state["fp_target"] = fp_identifier
                            st.success(f"📲 OTP Sent to {fp_identifier}! (Simulated OTP: {otp_val})")
                            st
