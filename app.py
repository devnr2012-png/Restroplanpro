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
    msg_body = f"RestoPlan Pro OTP: {otp_val}. Valid for 5 mins."
    payload = {
        "message": msg_body,
        "language": "english",
        "route": "q",
        "numbers": clean_num
    }
    headers = {
        'authorization': FAST2SMS_KEY.strip(),
        'Content-Type': "application/x-www-form-urlencoded"
    }
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=8)
        data = res.json()
        if data.get("return") is True:
            return True, "SMS sent to mobile successfully!"
        else:
            err = data.get("message
