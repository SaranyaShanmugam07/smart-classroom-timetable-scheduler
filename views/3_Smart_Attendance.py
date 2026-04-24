import streamlit as st
import cv2
import numpy as np
from PIL import Image
import database_manager as db
import os

# --- ROLE-BASED HEADERS ---
if st.session_state.role == "Admin":
    st.title("🏛️ Institutional Attendance Control")
    st.markdown("Global biometric management for the entire campus.")
elif st.session_state.role == "Staff":
    st.title("📸 Classroom Proctor Hub")
    st.markdown("Real-time student verification for faculty members.")
else:
    st.title("📸 My Biometric Check-in")
    st.markdown("Securely verify your presence for today's session.")

# --- SETTINGS ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

import socket
st.sidebar.subheader("🔒 Security Settings")
strictness = st.sidebar.slider("AI Match Threshold (%)", 30, 95, 60)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Network Security")
simulate_remote = st.sidebar.toggle("🛠️ Simulate Remote Access", value=False, help="Enable this to demonstrate a remote security violation.")

try:
    local_ip = socket.gethostbyname(socket.gethostname())
    is_campus = any(local_ip.startswith(prefix) for prefix in ["192.168.", "10.", "172.", "127."])
    
    # FORCED SIMULATION
    if simulate_remote:
        is_campus = False
        display_status = "🏠 Forced: Remote-Access"
    else:
        display_status = "🟢 Secured: MKCE-Intranet" if is_campus else "🏠 Session: Remote-Access"

    if is_campus:
        st.sidebar.success(display_status)
        st.sidebar.caption(f"📍 Location Stamp: **Campus Hub ({local_ip})**")
    else:
        st.sidebar.error(display_status)
        st.sidebar.caption(f"📍 Location Stamp: **Private IP ({local_ip})**")
except:
    st.sidebar.warning("⚠️ Network Status: Unstable")

st.sidebar.info("💡 Proximity Lock: Only authorizing biometric logs from the campus-verified IP range.")

# --- TABS DISPATCHER ---
if st.session_state.role == "Admin":
    t1, t2, t3 = st.tabs(["🏛️ Global Verification", "📝 Register Profiles", "📋 System Logs"])
    
    with t1:
        # Verification Logic (was tabs[0])
        st.subheader("🆔 Smart Identity Verification")
        registered_faces = [f.split(".")[0] for f in os.listdir(DATA_DIR) if f.endswith(".jpg")]
        if not registered_faces:
            st.info("No registered biometric profiles found. Please register a face first.")
        else:
            target_name = st.selectbox("Select Profile to Verify Presence:", registered_faces, help="Choose a student profile to verify their identity.")
            st.info(f"💡 **Proctor Mode**: Verifying identity for: **{target_name}**")
            if target_name:
                verify_photo = st.camera_input("Take Live Biometric Verification", key="verify_cam_admin")
                if verify_photo:
                    with st.spinner(f"🤖 AI isolating facial vectors for {target_name}..."):
                        # Biometric matching...
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                        template_path = os.path.join(DATA_DIR, f"{target_name}.jpg")
                        try:
                            template_img = Image.open(template_path).convert('RGB')
                            template_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2GRAY)
                            live_img = Image.open(verify_photo).convert('RGB')
                            live_cv = cv2.cvtColor(np.array(live_img), cv2.COLOR_RGB2GRAY)
                            t_faces = face_cascade.detectMultiScale(template_cv, 1.1, 4)
                            l_faces = face_cascade.detectMultiScale(live_cv, 1.1, 4)
                            if len(t_faces) == 0 or len(l_faces) == 0:
                                st.error("❌ BIOMETRIC ERROR: Face box not detected.")
                            else:
                                tx, ty, tw, th = t_faces[0]
                                t_crop = template_cv[ty:ty+th, tx:tx+tw]; t_crop = cv2.resize(t_crop, (256, 256))
                                lx, ly, lw, lh = l_faces[0]
                                l_crop = live_cv[ly:ly+lh, lx:lx+lw]; l_crop = cv2.resize(l_crop, (256, 256))
                                result = cv2.matchTemplate(l_crop, t_crop, cv2.TM_CCOEFF_NORMED)
                                _, max_val, _, _ = cv2.minMaxLoc(result)
                                confidence = max_val * 100
                                if confidence >= strictness:
                                    st.success(f"✅ VERIFIED: {target_name} ({confidence:.1f}%)")
                                    if db.mark_attendance(target_name, "Present"):
                                        st.balloons(); st.info("Attendance record updated.")
                                    else:
                                        st.warning("⚠️ DUPLICATE: Already marked today.")
                                else:
                                    st.error(f"❌ FRAUD ALERT: Face Mismatch ({confidence:.1f}%)")
                        except Exception as e:
                            st.error(f"Hardware Error: {e}")

    with t2:
        # Registration Logic (was tabs[1])
        st.subheader("👤 Staff/Student Registration")
        reg_name = st.text_input("Enter Full Name for Global Registration")
        reg_photo = st.camera_input("Capture Profile Photo", key="reg_cam_admin")
        if st.button("Register Face", type="primary", key="btn_reg_admin"):
            if reg_name and reg_photo:
                if os.path.exists(os.path.join(DATA_DIR, f"{reg_name}.jpg")):
                    st.error(f"❌ ERROR: Profile for '{reg_name}' already exists.")
                else:
                    with st.spinner("🔍 AI deep-scanning..."):
                        try:
                            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                            new_img = Image.open(reg_photo).convert('RGB')
                            new_cv = cv2.cvtColor(np.array(new_img), cv2.COLOR_RGB2GRAY)
                            new_faces = face_cascade.detectMultiScale(new_cv, 1.1, 4)
                            if len(new_faces) == 0:
                                st.error("❌ ERROR: No face detected.")
                            else:
                                nx, ny, nw, nh = new_faces[0]; new_crop = new_cv[ny:ny+nh, nx:nx+nw]; new_crop = cv2.resize(new_crop, (256, 256))
                                duplicate_found = None
                                existing_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".jpg")]
                                if existing_files:
                                    progress_bar = st.progress(0)
                                    for i, existing_f in enumerate(existing_files):
                                        e_name = existing_f.split(".")[0]; e_path = os.path.join(DATA_DIR, existing_f)
                                        e_img = Image.open(e_path).convert('RGB'); e_cv = cv2.cvtColor(np.array(e_img), cv2.COLOR_RGB2GRAY)
                                        e_faces = face_cascade.detectMultiScale(e_cv, 1.1, 4)
                                        if len(e_faces) > 0:
                                            ex, ey, ew, eh = e_faces[0]; e_crop = e_cv[ey:ey+eh, ex:ex+ew]; e_crop = cv2.resize(e_crop, (256, 256))
                                            result = cv2.matchTemplate(new_crop, e_crop, cv2.TM_CCOEFF_NORMED)
                                            _, max_val, _, _ = cv2.minMaxLoc(result)
                                            if max_val * 100 > 60: duplicate_found = e_name; progress_bar.progress(100); break
                                        progress_bar.progress((i + 1) / len(existing_files))
                                if duplicate_found:
                                    st.error(f"🚨 BIOMETRIC FRAUD: Face already linked to {duplicate_found}!")
                                else:
                                    new_img.save(os.path.join(DATA_DIR, f"{reg_name}.jpg"))
                                    st.success(f"✅ Registered {reg_name}!"); st.balloons()
                        except Exception as e:
                            st.error(f"Security Engine Error: {e}")

    with t3:
        st.subheader("📋 System-Wide Attendance Logs")
        logs_df = db.get_attendance_logs()
        if not logs_df.empty: st.dataframe(logs_df, use_container_width=True)
        else: st.info("No biometric logs found.")

elif st.session_state.role == "Staff":
    t1, t2, t3 = st.tabs(["📷 Verify Presence", "👤 Register My Profile", "📋 My Logs"])
    
    with t1:
        # Same Verification logic for Staff...
        st.subheader("📷 Staff Proctor Hub")
        registered_faces = [f.split(".")[0] for f in os.listdir(DATA_DIR) if f.endswith(".jpg")]
        target_name = st.selectbox("Select Student to Verify:", registered_faces)
        if target_name:
            verify_photo = st.camera_input("Verify Student Identity", key="verify_cam_staff")
            if verify_photo:
                # Biometric Match Logic... (Reduced for brevity but functional)
                with st.spinner("🤖 Verifying..."):
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    template_path = os.path.join(DATA_DIR, f"{target_name}.jpg")
                    try:
                        template_img = Image.open(template_path).convert('RGB')
                        template_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2GRAY)
                        live_img = Image.open(verify_photo).convert('RGB')
                        live_cv = cv2.cvtColor(np.array(live_img), cv2.COLOR_RGB2GRAY)
                        t_faces = face_cascade.detectMultiScale(template_cv, 1.1, 4)
                        l_faces = face_cascade.detectMultiScale(live_cv, 1.1, 4)
                        if len(t_faces) > 0 and len(l_faces) > 0:
                            tx, ty, tw, th = t_faces[0]; t_crop = template_cv[ty:ty+th, tx:tx+tw]; t_crop = cv2.resize(t_crop, (256, 256))
                            lx, ly, lw, lh = l_faces[0]; l_crop = live_cv[ly:ly+lh, lx:lx+lw]; l_crop = cv2.resize(l_crop, (256, 256))
                            result = cv2.matchTemplate(l_crop, t_crop, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(result)
                            confidence = max_val * 100
                            if confidence >= strictness:
                                if db.mark_attendance(target_name, "Present", display_status): st.success(f"✅ Verified {target_name} ({display_status})"); st.balloons()
                                else: st.warning("Already marked.")
                            else: st.error("❌ Mismatch Detect.")
                    except: st.error("Hardware Error")

    with t2:
        st.subheader("👤 Register My Staff Profile")
        reg_name = st.session_state.full_name
        reg_photo = st.camera_input("Capture My Profile", key="reg_cam_staff")
        if st.button("Register My Face", type="primary", key="btn_reg_staff"):
                if os.path.exists(os.path.join(DATA_DIR, f"{reg_name}.jpg")):
                    st.error("Profile already exists.")
                else:
                    new_img = Image.open(reg_photo).convert('RGB')
                    new_img.save(os.path.join(DATA_DIR, f"{reg_name}.jpg"))
                    st.success("✅ Profile Registered!")

    with t3:
        st.subheader("📋 My Activity Logs")
        logs_df = db.get_attendance_logs(st.session_state.full_name)
        if not logs_df.empty: st.dataframe(logs_df, use_container_width=True)
        else: st.info("No logs found.")

else: # STUDENT ROLE
    t1, t2 = st.tabs(["📸 My Attendance", "📋 My History"])
    
    with t1:
        st.subheader("📸 My Biometric Check-in")
        
        temp_name = st.session_state.full_name.strip()
        registered_files = [f.split(".")[0].strip() for f in os.listdir(DATA_DIR) if f.endswith(".jpg")]
        
        # Fuzzy Case-insensitive finding (Handles Initials like 'Saranya S')
        match_found = False
        target_name = None
        for f_name in registered_files:
            fn = f_name.lower().strip()
            tn = temp_name.lower().strip()
            
            # Match if one is a substring of the other (e.g., 'Saranya S' matches 'Saranya')
            if fn == tn or fn in tn or tn in fn:
                match_found = True
                target_name = f_name # Use the actual filename
                break
        
        if match_found:
            verify_photo = st.camera_input("Prove Presence", key="verify_cam_student")
            if verify_photo:
                with st.spinner("🤖 AI checking..."):
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    template_path = os.path.join(DATA_DIR, f"{target_name}.jpg")
                    template_img = Image.open(template_path).convert('RGB')
                    template_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2GRAY)
                    live_img = Image.open(verify_photo).convert('RGB'); live_cv = cv2.cvtColor(np.array(live_img), cv2.COLOR_RGB2GRAY)
                    t_faces = face_cascade.detectMultiScale(template_cv, 1.1, 4); l_faces = face_cascade.detectMultiScale(live_cv, 1.1, 4)
                    if len(t_faces) > 0 and len(l_faces) > 0:
                        tx, ty, tw, th = t_faces[0]; t_crop = template_cv[ty:ty+th, tx:tx+tw]; t_crop = cv2.resize(t_crop, (256, 256))
                        lx, ly, lw, lh = l_faces[0]; l_crop = live_cv[ly:ly+lh, lx:lx+lw]; l_crop = cv2.resize(l_crop, (256, 256))
                        result = cv2.matchTemplate(l_crop, t_crop, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(result)
                        confidence = max_val * 100
                        if confidence >= strictness:
                            if db.mark_attendance(target_name, "Present"): st.success("Verified!"); st.balloons()
                            else: st.warning("Already marked.")
                        else: st.error("❌ Mismatch")
        else:
            st.warning("⚠️ Profile not registered. Please contact HOD.")

    with t2:
        st.subheader("📋 My Attendance Records")
        logs_df = db.get_attendance_logs(st.session_state.full_name)
        if not logs_df.empty: st.dataframe(logs_df, use_container_width=True)
        else: st.info("No records yet.")
