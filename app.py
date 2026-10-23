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

# --- DATABASE SETUP (AUTO FIX & COMPATIBILITY) ---
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

# 3. Standard Clean White & Charcoal Black Modern Theme
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
    letter-spacing: -0.5px;
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
    transition: all 0.2s ease-in-out;
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
                        c.execute("SELECT username FROM users WHERE identifier = ?", (fp_identifier,))
                        user = c.fetchone()
                        if user:
                            otp_val = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO otps (identifier, otp) VALUES (?, ?)", (fp_identifier, otp_val))
                            conn.commit()
                            st.session_state["otp_sent"] = True
                            st.session_state["fp_target"] = fp_identifier
                            st.success(f"📲 OTP Sent to {fp_identifier}! (Simulated OTP: {otp_val})")
                            st.rerun()
                        else:
                            st.error("❌ Mobile Number/Email not registered.")
                    else:
                        st.error("Please enter your registered Mobile/Email.")
            else:
                st.write(f"OTP sent to: **{st.session_state.get('fp_target', '')}**")
                entered_otp = st.text_input("Enter 4-digit OTP", key="entered_otp")
                new_pass = st.text_input("Set New Password", type="password", key="new_pass")
                
                if st.button("Verify OTP & Change Password", use_container_width=True, key="verify_otp_btn"):
                    c.execute("SELECT otp FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                    row = c.fetchone()
                    if row and row[0] == entered_otp:
                        if new_pass:
                            hashed_new = hash_password(new_pass)
                            c.execute("UPDATE users SET password = ? WHERE identifier = ?", (hashed_new, st.session_state["fp_target"]))
                            c.execute("DELETE FROM otps WHERE identifier = ?", (st.session_state["fp_target"],))
                            conn.commit()
                            st.session_state["otp_sent"] = False
                            st.success("✅ Password reset successfully! Please switch to Login tab.")
                        else:
                            st.error("Please enter a new password.")
                    else:
                        st.error("❌ Invalid OTP. Please try again.")
                        
                if st.button("Resend OTP / Change Number", key="reset_fp_state"):
                    st.session_state["otp_sent"] = False
                    st.rerun()
                        
        conn.close()
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        utilities = st.number_input(f"Utilities & Marketing ({currency})", value=30000, step=1000)
    total_opex = rent + staffing + raw_materials + utilities
    working_capital = total_opex * 3
    st.warning(f"**Total Monthly OpEx:** {currency} {total_opex:,.2f} | **Working Capital Reserve (3 Months):** {currency} {working_capital:,.2f}")

grand_total = total_capex + working_capital

def display_payment_gateway(unique_tab_key):
    st.markdown('<div class="locked-section">', unsafe_allow_html=True)
    st.error("🔒 **VIP PRO FEATURE LOCKED — UNLOCK FULL BENEFITS IN JUST ₹250 ($3)**")
    
    b_col1, b_col2, b_col3 = st.columns(3)
    b_col1.success("📊 **Benefit 1:** Interactive CapEx vs Working Capital Charts")
    b_col2.info("🎯 **Benefit 2:** Exact ROI Payback Months & Net Profit Projections")
    b_col3.warning("📥 **Benefit 3:** 1-Click Bank Loan & Investor Ready `resturant.xlsx`")
    
    st.markdown("---")
    pay_col1, pay_col2 = st.columns(2)
    
    with pay_col1:
        st.subheader("Method 1: Pay via UPI (India)")
        upi_id = "9335845451@indie" 
        upi_name = "Devendra Srivastava"
        amount = "250"
        
        upi_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(upi_name)}&am={amount}&cu=INR"
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(upi_url)}"
        
        st.image(qr_code_url, caption=f"Scan to pay ₹{amount}")
        st.write(f"UPI ID: `{upi_id}`")
        
    with pay_col2:
        st.subheader("Method 2: Pay via PayPal (International)")
        paypal_email = "devssconsulting@gmail.com"
        paypal_amount = "3"
        paypal_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={urllib.parse.quote(paypal_email)}&currency_code=USD&amount={paypal_amount}&item_name=RestoPlan+Pro+Unlock"
        
        st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#0F172A; color:white; padding:10px 20px; border:none; border-radius:6px; font-size:15px; cursor:pointer;">Pay $3 via PayPal</button></a>', unsafe_allow_html=True)
        st.write("---")
        st.write("Done with payment? Enter your Transaction ID below to verify and unlock.")
        
        tx_id = st.text_input("Transaction / UPI Reference ID", key=f"tx_id_input_{unique_tab_key}")
        if st.button("Verify & Unlock Pro Benefits", key=f"tx_btn_{unique_tab_key}"):
            if len(tx_id) > 4: 
                st.session_state["is_paid"] = True
                st.rerun()
            else:
                st.error("Invalid Transaction ID. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    if not st.session_state["is_paid"]:
        display_payment_gateway("tab3")
    else:
        st.success("✅ Payment Verified. Welcome to VIP Pro Analytics!")
        capex_data = {"Category": ["Capital Expenditure", "Working Capital (3M)"], "Amount": [total_capex, working_capital]}
        fig_capex = px.pie(capex_data, values="Amount", names="Category", title="Total Investment Breakdown", hole=0.4)
        st.plotly_chart(fig_capex, use_container_width=True)
        
        st.write(f"### 💰 Net Startup Investment Required: {currency} {grand_total:,.2f}")
        st.info("🎯 **ROI Calculator:** Assuming a 15% monthly net margin, your estimated payback period is **8 to 10 months**.")

with tab4:
    if not st.session_state["is_paid"]:
        display_payment_gateway("tab4")
    else:
        st.success("✅ Pro Feature Unlocked. Download your Bank & Investor Ready Excel Blueprint below.")
        
        def create_excel():
            data = {
                "Budget Element": [
                    "Security Deposit", "Furniture & Interior", "Kitchen Equipment", "Licenses & POS", 
                    "Monthly Rent", "Staff Salary", "Raw Materials", "Utilities & Marketing", 
                    "Working Capital Reserve (3 Months)", "GRAND TOTAL INVESTMENT"
                ],
                f"Amount ({currency})": [
                    deposit, interior, kitchen_eq, licenses, 
                    rent, staffing, raw_materials, utilities, 
                    working_capital, grand_total
                ]
            }
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="RestoPlan_Budget")
            return output.getvalue()

        excel_file = create_excel()
        st.download_button(
            label="📥 Download resturant.xlsx Blueprint",
            data=excel_file,
            file_name="resturant.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab5:
    st.subheader("📍 Location Intelligence & Top 5 Verified Vendors")
    st.write("Find out the best commercial spots in your city and connect directly with verified top-tier vendors for your restaurant startup.")
    
    user_city = st.text_input("Enter Your Target City / Location (e.g., Prayagraj, Delhi, Mumbai):", value="Prayagraj")
    business_model = st.selectbox("Select Business Type for Vendor Sourcing:", ["Cloud Kitchen", "Fine Dining Restaurant", "Cafe & Bakery", "QSR & Food Truck"])
    
    if st.button("🔍 Analyze Location & Find Top 5 Vendors", use_container_width=True):
        st.success(f"📍 **Optimal Business Hubs in {user_city}:**")
        st.markdown(f"""
        * **Hub 1 (High Footfall / Delivery Zone):** Civil Lines / Main Commercial Market (Estimated Footfall: High, Rental Yield: Moderate).
        * **Hub 2 (Budget-Friendly / Cloud Kitchen Zone):** Transport Nagar / Outskirts Delivery Hub (Low Rent, Fast Logistics Access).
        * **Hub 3 (Youth / Student Hub):** University Road / Cafeteria Alley (High demand for Cafe & QSR models).
        """)
        
    st.markdown("---")
    
    if not st.session_state["mega_plan_active"]:
        st.markdown(
            '<div class="mega-banner">'
            '<h2>🚀 Unlock Mega Solution Plan ($12 / ₹1,100)</h2>'
            '<p>Get direct contact details of the <b>Top 5 Verified Vendors</b> for Kitchen Equipment, Raw Materials, Interiors, and POS Systems, plus direct vendor-to-founder calling features!</p>'
            '</div>',
            unsafe_allow_html=True
        )
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown("### Pay via UPI (₹1,100 INR)")
            mega_upi = "9335845451@indie"
            mega_upi_url = f"upi://pay?pa={mega_upi}&pn=Devendra%20Srivastava&am=1100&cu=INR"
            mega_qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(mega_upi_url)}"
            st.image(mega_qr, caption="Scan & Pay ₹1,100")
            st.write(f"UPI ID: `{mega_upi}`")
            
        with m_col2:
            st.markdown("### Pay via PayPal ($12 USD)")
            paypal_email = "devssconsulting@gmail.com"
            paypal_amount = "12"
            paypal_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={urllib.parse.quote(paypal_email)}&currency_code=USD&amount={paypal_amount}&item_name=Mega+Solution+Plan"
            
            st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#0F172A; color:white; padding:12px 24px; border:none; border-radius:6px; font-size:15px; cursor:pointer; font-weight:bold;">Pay $12 via PayPal</button></a>', unsafe_allow_html=True)
            st.write("---")
            mega_tx = st.text_input("Enter Mega Plan Transaction ID", key="mega_tx_input")
            if st.button("Verify & Activate Mega Solution Plan", key="verify_mega_btn"):
                if len(mega_tx) > 4:
                    st.session_state["mega_plan_active"] = True
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET mega_plan = 1 WHERE identifier = ?", (st.session_
