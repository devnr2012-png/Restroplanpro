import streamlit as st
import streamlit.components.v1 as components
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT,
            identifier TEXT UNIQUE,
            password TEXT,
            mega_plan INTEGER DEFAULT 0
        )
    ''')
    try:
        c.execute('ALTER TABLE users ADD COLUMN mega_plan INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            identifier TEXT PRIMARY KEY,
            otp TEXT
        )
    ''')
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

# 3. Clean White & Charcoal Black Standard Theme CSS
css_rules = """
<style>
[data-testid='stAppViewContainer'] {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}
[data-testid='stHeader'] { 
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0;
}
body, p, span, label, div {
    color: #1E293B !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
.side-card { 
    background: #FFFFFF !important; 
    border: 1px solid #E2E8F0 !important; 
    border-radius: 14px !important; 
    padding: 24px !important; 
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06) !important; 
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
.mega-banner h2, .mega-banner p, .mega-banner b {
    color: #FFFFFF !important;
}
button[kind="primary"], .stButton > button {
    background-color: #0F172A !important;
    color: #FFFFFF !important;
    border: 1px solid #0F172A !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
button[kind="primary"]:hover, .stButton > button:hover {
    background-color: #B45309 !important;
    border-color: #B45309 !important;
    color: #FFFFFF !important;
}
</style>
"""
st.markdown(css_rules, unsafe_allow_html=True)

# Logo Display Section
col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown('<div style="text-align: center; font-size: 42px;">🍽️</div>', unsafe_allow_html=True)
    st.markdown('<div class="title-text">RestoPlan Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">ULTIMATE RESTAURANT STARTUP BUDGET & ROI ANALYZER</div>', unsafe_allow_html=True)

# 4. Standard User Registration, Login & Forgot Password System
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
            
    with col_right:
        st.markdown('<div class="side-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='color: #0F172A; margin-top: 0px;'>🔐 Secure Account Portal</h3>", unsafe_allow_html=True)
        auth_action = st.radio("Select Action", ["Login", "Register", "Forgot Password"], horizontal=True, key="auth_action_radio")
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        if auth_action == "Register":
            st.info("Create your account using your Name, Mobile/Email and Password.")
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_identifier = st.text_input("Mobile Number or Email", key="reg_identifier")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            
            if st.button("Register Now", use_container_width=True, key="reg_btn"):
                if reg_name and reg_identifier and reg_pass:
                    c.execute("SELECT * FROM users WHERE identifier = ?", (reg_identifier,))
                    existing = c.fetchone()
                    if existing:
                        st.error("⚠️ An account with this Mobile/Email already exists! Please login.")
                    else:
                        hashed_pw = hash_password(reg_pass)
                        c.execute("INSERT INTO users (username, identifier, password, mega_plan) VALUES (?, ?, ?, 0)", (reg_name, reg_identifier, hashed_pw))
                        conn.commit()
                        st.success("✅ Registration Successful! Please switch to Login tab.")
                else:
                    st.error("Please fill in all details.")
                    
        elif auth_action == "Login":
            st.info("Log in with your registered Mobile Number/Email and Password.")
            log_identifier = st.text_input("Mobile Number or Email", key="log_identifier")
            log_pass = st.text_input("Password", type="password", key="log_pass")
            
            if st.button("Login", use_container_width=True, key="log_btn"):
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
                        st.error("❌ Invalid credentials or user not registered.")
                else:
                    st.error("Please enter both Mobile/Email and Password.")
                    
        elif auth_action == "Forgot Password":
            st.info("Reset your password using an OTP sent to your Mobile/Email.")
            fp_identifier = st.text_input("Registered Mobile Number or Email", key="fp_identifier")
            
            if not st.session_state["otp_sent"]:
                if st.button("Send OTP", use_container_width=True, key="send_otp_btn"):
                    if fp_identifier:
                        c.execute("SELECT username FROM users WHERE identifier = ?", (fp
