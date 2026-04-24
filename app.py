import streamlit as st
import database_manager as db
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Smart Classroom AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL WHITE CSS ---
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* Clean Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Center Login Card */
    .login-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 40px;
        background: #FFFFFF;
        border-radius: 24px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        border: 1px solid #F1F5F9;
    }
    
    /* Premium Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 12px 24px;
        background: #2563EB;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: #1D4ED8;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* Input Styling */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        padding: 10px 15px;
    }
    
    /* Tabs for Login/Signup */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #64748B;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        border-bottom-color: #2563EB !important;
    }

    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE INIT ---
if 'db_init' not in st.session_state:
    db.initialize_db()
    st.session_state.db_init = True

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.full_name = None
    st.session_state.sim_day = "Monday" # Default simulation day

def login_ui():
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='margin-bottom: 5px;'>🎓 Smart Class Room and Time Table Scheduler</h1>
                <p style='color: #64748B; font-size: 1.1rem;'>Professional Academic Management Portal (MKCE)</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Enter Portal")
                
                if submit:
                    success, role, full_name = db.login(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.role = role
                        st.session_state.username = username
                        st.session_state.full_name = full_name
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")

        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Choose Username")
                new_full_name = st.text_input("Full Name / Staff Name")
                new_password = st.text_input("Create Password", type="password")
                new_role = st.selectbox("Role", ["Student", "Staff", "Admin"])
                secret_code = st.text_input("College Secret Code", help="Ask your administrator for the code.")
                signup_submit = st.form_submit_button("Create Account")
                
                if signup_submit:
                    success, message = db.signup(new_username, new_password, new_full_name, secret_code, new_role)
                    if success:
                        st.success(f"✅ {message}! Please login.")
                    else:
                        st.error(f"❌ {message}")

if not st.session_state.logged_in:
    login_ui()
else:
    # --- NAVIGATION ---
    st.sidebar.markdown(f"""
        <div style='background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>👋 Welcome</h2>
            <p style='margin: 0; opacity: 0.9;'>{st.session_state.full_name}</p>
            <div style='font-size: 0.8rem; margin-top: 5px; opacity: 0.8; text-transform: uppercase;'>Role: {st.session_state.role}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Define Pages
    dashboard = st.Page("views/1_Dashboard.py", title="Analytics Dashboard", icon="📊")
    timetable = st.Page("views/2_AI_Timetable.py", title="Dynamic Timetable", icon="📅")
    attendance = st.Page("views/3_Smart_Attendance.py", title="AI Attendance", icon="📸")
    engagement = st.Page("views/4_Engagement_AI.py", title="Focus Monitor", icon="🧠")
    
    if st.session_state.role == "Admin":
        pg = st.navigation([dashboard, timetable, attendance, engagement])
    elif st.session_state.role == "Staff":
        # Staff have full suite including Proxy Hub and Attendance Monitoring
        pg = st.navigation([dashboard, timetable, attendance, engagement])
    else:
        # Students see Timetable (to track proxy/rooms) and Attendance (to check-in)
        pg = st.navigation([timetable, attendance])
        
    if st.sidebar.button("Logout", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
        
    pg.run()
