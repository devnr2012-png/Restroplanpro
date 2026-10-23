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

# --- FAST2SMS API KEY INTEGRATED ---
FAST2SMS_API_KEY = "Rg7N51LZuhDCFWsMEorwmBHdpGSye802XnlVP3qU9azA4v6JkY9Eun8zWR4VZq1pdCaeAJUmB27QNFXM"

def send_sms_otp(mobile_number, otp_code):
    """Sends OTP to Indian mobile numbers via Fast2SMS Quick OTP route."""
    clean_mobile = "".join(filter(str.isdigit, str(mobile_number)))
    if len(clean_mobile) == 12 and clean_mobile.startswith("91"):
        clean_mobile = clean_mobile[2:]
    
    if len(clean_mobile) != 10:
        return False, "Kripya 10-digit ka valid mobile number dalein."

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "variables_values": str(otp_code),
        "route": "otp",
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
            return True, "SMS aapke mobile par bhej diya gaya hai!"
        else:
            msg = res_json.get("message", "API Error")
            if isinstance(msg, list) and len(msg) > 0:
                msg = msg[0]
            return False, f"Fast2SMS Alert: {msg}"
    except Exception as e:
        return False, f"Network error: {str(e)}"

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
    margin-bottom: 2
