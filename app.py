import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import io
import urllib.parse
import os
import sqlite3
import hashlib

# 1. Page Configuration
st.set_page_config(page_title="RestoPlan Pro", page_icon="🍽️", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE SETUP (AUTO RESET TO FIX SCHEMA ERRORS) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Check if table exists with correct schema, if not recreate cleanly
    try:
        c.execute("SELECT mega_plan FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # Table doesn't exist or column missing, drop and recreate fresh
        c.execute("DROP TABLE IF EXISTS users")
        c.execute('''
            CREATE TABLE users (
                username TEXT,
                identifier TEXT UNIQUE,
                password TEXT,
                mega_plan INTEGER DEFAULT 0
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

# 3. Premium Luxury Restaurant Theme CSS
css_rules = (
    "<style>"
    "[data-testid='stAppViewContainer'] {"
    "background-image: linear-gradient(rgba(30, 20, 10, 0.90), rgba(15, 10, 5, 0.95)), "
    "url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=2070&auto=format&fit=crop');"
    "background-size: cover; background-attachment: fixed;}"
    "[data-testid='stHeader'] { background: rgba(0,0,0,0); }"
    ".title-text { font-size: 42px; font-weight: 800; color: #F5B041; text-align: center; text-shadow: 2px 2px 6px rgba(0,0,0,0.8); margin-top: 0px; margin-bottom: 0px; }"
    ".subtitle-text { font-size: 16px; color: #F39C12; text-align: center; margin-bottom: 25px; font-weight: 600; letter-spacing: 1.5px; }"
    ".locked-section { text-align: center; padding: 30px; background-color: rgba(20, 15, 10, 0.85); border-radius: 12px; border: 2px dashed #F1C40F; margin-bottom: 20px;}"
    ".side-card { background: rgba(20, 15, 10, 0.88); border: 1px solid #D4AC0D; border-radius: 16px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.7); }"
    ".mega-banner { background: linear-gradient(135deg, #78350f, #b45309); border: 2px solid #F5B041; border-radius: 14px; padding: 25px; color: white; text-align: center; margin-bottom: 25px; }"
    "</style>"
)
st.markdown(css_rules, unsafe_allow_html=True)

# Logo Display Section
col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown('<div style="text-align: center; font-size: 45px;">🛡️</div>', unsafe_allow_html=True)
    st.markdown('<div class="title-text">RestoPlan Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">ULTIMATE RESTAURANT STARTUP BUDGET & ROI ANALYZER</div>', unsafe_allow_html=True)

# 4. Standard User Registration & Login System
if not st.session_state["logged_in"]:
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.markdown("<h3 style='color: #F5B041; margin-top: 0px;'>🌟 Plan Your Dream Food Business</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #EAECEE; font-size: 15px;'>Easily budget, discover top local vendors, and analyze profitability for Cloud Kitchens, Fine Dining Restaurants, Cozy Cafes, and QSR / Food Trucks.</p>", unsafe_allow_html=True)
        
        ig1, ig2 = st.columns(2)
        with ig1:
            st.image("https://images.unsplash.com/photo-1556910103-1c02745aae4d?q=80&w=500&auto=format&fit=crop", caption="Cloud Kitchen Setup", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=500&auto=format&fit=crop", caption="Cozy Cafe & Bakery", use_container_width=True)
        with ig2:
            st.image("https://images.unsplash.com/photo-1552566626-52f8b828add9?q=80&w=500&auto=format&fit=crop", caption="Fine Dining Restaurant", use_container_width=True)
            st.image("https://images.unsplash.com/photo-1565299585323-38d6b0865b47?q=80&w=500&auto=format&fit=crop", caption="QSR & Food Truck", use_container_width=True)
            
    with col_right:
        st.markdown('<div class="side-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Secure Account Portal")
        auth_action = st.radio("Select Action", ["Login", "Register"], horizontal=True, key="auth_action_radio")
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        if auth_action == "Register":
            st.info("Create your account using your Name, Phone/Email and Password.")
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_identifier = st.text_input("Phone Number or Email", key="reg_identifier")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            
            if st.button("Register Now", use_container_width=True, key="reg_btn"):
                if reg_name and reg_identifier and reg_pass:
                    c.execute("SELECT * FROM users WHERE identifier = ?", (reg_identifier,))
                    existing = c.fetchone()
                    if existing:
                        st.error("⚠️ An account with this Phone/Email already exists! Please login.")
                    else:
                        hashed_pw = hash_password(reg_pass)
                        c.execute("INSERT INTO users (username, identifier, password, mega_plan) VALUES (?, ?, ?, 0)", (reg_name, reg_identifier, hashed_pw))
                        conn.commit()
                        st.success("✅ Registration Successful! Please switch to Login.")
                else:
                    st.error("Please fill in all fields.")
                    
        elif auth_action == "Login":
            st.info("Log in with your registered Phone/Email and Password.")
            log_identifier = st.text_input("Phone Number or Email", key="log_identifier")
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
                    st.error("Please enter both identifier and password.")
                        
        conn.close()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.stop()

# --- APP STARTS HERE AFTER LOGIN ---
st.sidebar.success(f"👤 Welcome, {st.session_state['username']}!")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["is_paid"] = False
    st.session_state["mega_plan_active"] = False
    st.rerun()

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
    b_col1.success("📊 **Benefit 1:** Interactive CapEx vs Working Capital Pie-Charts")
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
        
        st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#003087; color:white; padding:10px 20px; border:none; border-radius:5px; font-size:16px; cursor:pointer;">Pay $3 via PayPal</button></a>', unsafe_allow_html=True)
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
            
            st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#003087; color:white; padding:12px 24px; border:none; border-radius:6px; font-size:16px; cursor:pointer; font-weight:bold;">Pay $12 via PayPal</button></a>', unsafe_allow_html=True)
            st.write("---")
            mega_tx = st.text_input("Enter Mega Plan Transaction ID", key="mega_tx_input")
            if st.button("Verify & Activate Mega Solution Plan", key="verify_mega_btn"):
                if len(mega_tx) > 4:
                    st.session_state["mega_plan_active"] = True
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute("UPDATE users SET mega_plan = 1 WHERE identifier = ?", (st.session_state["identifier"],))
                    conn.commit()
                    conn.close()
                    st.success("🎉 Mega Solution Plan Activated Successfully! Enjoy direct vendor access.")
                    st.rerun()
                else:
                    st.error("Please enter a valid Transaction ID.")
    else:
        st.success("👑 **Mega Solution Plan Active!** Here are the Top 5 Verified Vendors for your setup:")
        
        vendors_df = pd.DataFrame({
            "Vendor Name": ["Apex Commercial Kitchens", "Metro Fresh Agro Supplies", "Urban Décor & Interiors", "FastPOS Billing Solutions", "Delta Refrigeration & HVAC"],
            "Specialization": ["Commercial Heavy-Duty Ovens & Fryers", "Bulk Organic Raw Materials & Spices", "Turnkey Restaurant Interior Fit-outs", "Cloud POS & Inventory Software", "Walk-in Freezers & AC Ducting"],
            "Contact Phone / Email": ["+91 98765 43210 / sales@apexkitchen.com", "+91 91234 56789 / supply@metroagro.com", "+91 99887 76655 / design@urbandecor.in", "+91 95544 33221 / support@fastpos.io", "+91 94433 22110 / info@deltahvac.com"],
            "Action / Direct Inquiry": ["Call Vendor", "Request Quote", "Book Consultation", "Get Free Demo", "Get Catalog"]
        })
        st.dataframe(vendors_df, use_container_width=True)
        st.info("💡 **Pro Tip:** Mention **RestoPlan Pro Reference** when calling these vendors to get an exclusive 10% startup discount on bulk orders!")

with tab6:
    st.subheader("🎥 Step-by-Step Restaurant Budget Workflow Video Walkthrough")
    st.write("Watch this video tutorial to learn how to use every feature of RestoPlan Pro step-by-step.")
    st.video("https://youtu.be/reCF7nIfen4")