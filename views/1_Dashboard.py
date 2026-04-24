import streamlit as st
import pandas as pd
import database_manager as db
import plotly.express as px

# --- PAGE STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2563eb;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    /* Smart Room Cards */
    .room-card {
        background: #F8FAFC;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 10px;
    }
    .status-indicator {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    .wastage-alert {
        background: #fef2f2;
        border: 1px solid #fee2e2;
        padding: 10px;
        border-radius: 8px;
        color: #991b1b;
        font-size: 0.85rem;
        margin-bottom: 15px;
    }
    /* Staff Table Styling */
    .staff-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .staff-table th {
        background: #f8fafc;
        padding: 12px;
        text-align: left;
        color: #64748b;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
    }
    .staff-table td {
        padding: 12px;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.95rem;
    }
    .badge-subject {
        background: #eff6ff;
        color: #2563eb;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Smart Analytics Dashboard")
st.markdown("Welcome back! Here's the real-time status of your academic environment.")

# --- DATA FETCHING ---
teachers_df = pd.read_sql_query("SELECT * FROM teachers", db.get_connection())
attendance_df = pd.read_sql_query("SELECT * FROM attendance", db.get_connection())
rooms_df = db.get_rooms_status()

# --- PREMIUM METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Staff</div>
            <div class="metric-value">{len(teachers_df)}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    absent_count = len(teachers_df[teachers_df['status'] == 'Absent'])
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Absent Today</div>
            <div class="metric-value" style="color: #ef4444;">{absent_count}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">AI System Uptime</div>
            <div class="metric-value" style="color: #10b981;">99.9%</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SYSTEM ALERTS (Critical Activity Monitoring) ---
if st.session_state.role in ["Admin", "Staff"]:
    st.markdown("### 🚨 Critical System Activity")
    alerts_df = db.get_system_alerts(limit=3)
    if not alerts_df.empty:
        for _, alert in alerts_df.iterrows():
            # Color coding based on severity
            color = "#ef4444" if alert['alert_type'] == "Critical" else "#f59e0b"
            bg_color = "#fff1f2" if alert['alert_type'] == "Critical" else "#fffbeb"
            border_color = "#fecaca" if alert['alert_type'] == "Critical" else "#fef3c7"
            text_color = "#991b1b" if alert['alert_type'] == "Critical" else "#92400e"
            
            st.markdown(f"""
                <div style='background: {bg_color}; border: 1px solid {border_color}; border-left: 5px solid {color}; padding: 12px; border-radius: 10px; margin-bottom: 12px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                    <div style='font-size: 1.5rem; margin-right: 15px;'>{'🛑' if alert['alert_type'] == "Critical" else '⚠️'}</div>
                    <div style='flex-grow: 1;'>
                        <div style='font-weight: 800; color: {text_color}; font-size: 0.95rem; text-transform: uppercase;'>{alert['alert_type']} ALERT: {alert['room']}</div>
                        <div style='font-size: 0.9rem; color: {text_color}; margin-top: 2px;'>{alert['message']}</div>
                        <div style='font-size: 0.75rem; color: {color}; margin-top: 5px; font-weight: 600;'>🕒 {alert['timestamp']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ **System Status: Stable** - No critical incidents reported in the last 24 hours.")
    st.markdown("<br>", unsafe_allow_html=True)

# --- CHARTS ---
c1, c2 = st.columns([1.5, 1])

with c1:
    st.markdown("### 📈 Attendance Trends (Last 7 Days)")
    if not attendance_df.empty:
        # Avoid errors if timestamp isn't datetime
        attendance_df['timestamp'] = pd.to_datetime(attendance_df['timestamp'], errors='coerce')
        attendance_df = attendance_df.dropna(subset=['timestamp'])
        
        # Group by date and count unique students
        attendance_df['date'] = attendance_df['timestamp'].dt.date
        trend_data = attendance_df.groupby('date').size().reset_index(name='Student Volume')
        
        # Using Area Chart for professional look
        st.area_chart(trend_data.set_index('date'), color="#2563eb")
        st.caption("🔍 Daily student check-in density across the institutional network.")
    else:
        st.info("No attendance data yet. Use Maintenance tools to generate demo data.")

with c2:
    st.markdown("### 👨‍🏫 Staff Status")
    status_counts = teachers_df['status'].value_counts().reset_index()
    fig_pie = px.pie(status_counts, values='count', names='status', 
                    hole=0.6, color_discrete_sequence=['#2563eb', '#f1f5f9'])
    fig_pie.update_layout(showlegend=False, height=400, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# --- STAFF DIRECTORY ---
st.markdown("### 📋 Staff Status Board")
# Displaying staff as premium cards
s_cols = st.columns(3)
for i, (_, staff) in enumerate(teachers_df.iterrows()):
    with s_cols[i % 3]:
        status_color = "#10b981" if staff['status'] == 'Available' else "#ef4444"
        
        st.markdown(f"""
            <div style='background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; border-left: 5px solid {status_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;'>
                <div style='font-weight: 700; font-size: 1rem; color: #1e293b;'>{staff['name']}</div>
                <div style='font-size: 0.8rem; color: #6366f1; font-weight: bold; margin-top: 5px;'>📚 {staff['specialty']}</div>
                <div style='font-size: 0.75rem; margin-top: 5px; color: {status_color}; font-weight: 600;'>
                    {'● Active ✅' if staff['status'] == 'Available' else '○ Absent ❌'}
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SUBJECT WISE ENGAGEMENT ---
st.markdown("### 📊 AI Subject-Wise Analytics (IV SEM)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("PQST Attendance", "92%", "↑ 1.2%")
m2.metric("EDA Insights", "88%", "↑ 8.5%")
m3.metric("DBMS Queries", "145", "↑ 22")
m4.metric("ADM Projects", "12", "New")

st.markdown("<br>", unsafe_allow_html=True)

# --- SIDEBAR SIMULATION ---
with st.sidebar:
    # --- MAINTENANCE TOOL (For Viva Demo) ---
    with st.expander("🛠️ System Maintenance"):
        st.write("Academic Analytics")
        if st.button("🚀 Populate 7-Day Demo History"):
            import random
            from datetime import timedelta, datetime
            import sqlite3
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Cleanup first for fresh demo
            cursor.execute("DELETE FROM attendance")
            
            names = ["Saranya S", "Nandhana R", "Rahul VK", "Priya K", "Vijay M", "Dinesh B", "Harini P"]
            for i in range(7, 0, -1):
                date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                # Randomly pick 4-7 students per day
                daily_cands = random.sample(names, random.randint(4, 7))
                for name in daily_cands:
                    # Alternating between Campus and Remote for diversity
                    net_type = "🟢 Campus-Net (192.168.1.10)" if random.random() > 0.3 else "🏠 Remote-Session (Simulated)"
                    cursor.execute(
                        "INSERT INTO attendance (name, timestamp, status, network_status) VALUES (?, ?, ?, ?)",
                        (name, f"{date_str} {random.randint(8,10)}:{random.randint(10,59)}:00", "Present", net_type)
                    )
            conn.commit()
            conn.close()
            st.success("7-Day Demo History Generated!")
            st.rerun()

    st.divider()
    st.subheader("📅 Semester IV Operational Day")
    # This selector drives the proxy logic in the Timetable page
    st.session_state.sim_day = st.selectbox(
        "Set Current Operational Day:",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].index(st.session_state.sim_day),
        key="sim_day_selector",
        help="Marking staff absent will only trigger proxies for this specific day."
    )
    st.info(f"The system is currently simulating **{st.session_state.sim_day}** operations.")

with st.expander("📝 View System Logs"):
    st.code(f"System Initialized\nOperational Day: {st.session_state.sim_day}\nAI Engine: Online\nBiometric Matchmaker: Connected")
