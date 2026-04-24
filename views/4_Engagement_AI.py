import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import database_manager as db

# --- SECURITY BLOCK ---
if st.session_state.role == "Student":
    st.error("❌ ACCESS DENIED: Cognitive Analytics is restricted to Admin/Staff only.")
    st.info("💡 Your classroom engagement is being monitored securely for institutional audits.")
    st.stop()

# --- ROLE-BASED HEADERS ---
if st.session_state.role == "Admin":
    st.title("🏛️ Institutional Cognitive Hub")
    st.markdown("Monitoring the entire campus's engagement and energy levels.")
else:
    st.title("🧠 Classroom Focus Hub")
    st.markdown("Real-time monitoring of classroom attention and energy levels.")

# --- CLASSROOM MONITORING ---
room_source = st.selectbox("Select Camera Unit:", ["CR-101 (Main Block)", "CR-102 (Main Block)", "LAB-201 (CS-Block)", "LAB-202 (CS-Block)"])
st.info(f"💡 **Live AI Hub**: Monitoring classroom **{room_source}** in real-time. (Supports multi-student tracking)")
cam_feed = st.camera_input(f"📷 Active Feed: {room_source}", key="focus_cam")

if cam_feed:
    with st.spinner(f"🤖 AI analyzing facial vectors from {room_source}..."):
        # Process Image
        try:
            img = Image.open(cam_feed)
            img_array = np.array(img.convert('RGB'))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Load Cascades
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
            
            # Detect Faces
            faces = face_cascade.detectMultiScale(gray, 1.3, face_thresh if "face_thresh" in locals() else 5)
            
            if len(faces) == 0:
                st.error("❌ CLASSROOM STATUS: DISTRACTED / ABSENT")
                st.write("AI Vision: No students detected facing the board in this feed.")
                st.image(img_array, caption=f"Source: {room_source} - Empty Classroom", use_container_width=True)
            else:
                st.info(f"👥 **AI Tracking Enabled**: Monitoring **{len(faces)}** Student(s) in real-time.")
                
                # Global engagement stats
                attentive_count = 0
                drowsy_count = 0
                
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]
                    roi_color = img_array[y:y+h, x:x+w]
                    
                    e_thresh = eye_thresh if "eye_thresh" in locals() else 1.25
                    eyes = eye_cascade.detectMultiScale(roi_gray, e_thresh, 4)
                    
                    if len(eyes) == 0:
                        drowsy_count += 1
                        cv2.rectangle(img_array, (x, y), (x+w, y+h), (255, 0, 0), 4) # Red for Sleep
                    else:
                        attentive_count += 1
                        cv2.rectangle(img_array, (x, y), (x+w, y+h), (0, 255, 0), 4) # Green for Attentive
                        for (ex, ey, ew, eh) in eyes:
                            cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 255, 0), 2)
                
                # Classroom-level metrics
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Group Engagement", f"{ (attentive_count/len(faces))*100 :.1f}%")
                with c2:
                    st.metric("Total Observed", len(faces))
                
                if attentive_count >= drowsy_count:
                    st.success("✅ CLASSROOM STATUS: HIGH ATTENTION LOCKED")
                else:
                    st.warning("😴 CLASSROOM STATUS: LOW CONCENTRATION ALERT")
                    
                    # --- AUDIO ALERT ---
                    # Short professional "Notification" beep (Base64)
                    beep_html = """
                        <audio autoplay>
                            <source src="data:audio/mp3;base64,SUQzBAAAAAABAFRYWFgAAAASAAADbWFqb3JfYnJhbmQAZGFzaABUWFhYAAAAEAAAA21pbm9yX3ZlcnNpb24AMABUWFhYAAAAHAAAA2NvbXBhdGlibGVfYnJhbmRzAGlzbzZtcDQxAFRTU0UAAAAPAAADTGF2ZjYwLjEwMC4xMDAAAAAAAAAAAAAAA//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//vwZBAAABGIAAAMDAAAAA//+8GQQAAASiAAAHAwAAAAD//7wZBAAABIwAAAkDAAAAA//+8GQQAAAS8AAArAwAAAAD//7wZBAAABMAAAAsDAAAAA//+9GQQAAATWAAAHAwAAAAD//70ZBAAABOgAAAgDAAAAA//+9GQQAAAT6AAAkDAAAAA//+9GQQAAAUmAAArAwAAAAD//70ZBAAABSwAAAsDAAAAA//+9GQQAAAVmAAAHAwAAAAD//70ZBAAABWgAAAgDAAAAA//+9GQQAAAVwAAAkDAAAAA//+9GQQAAAV4AAArAwAAAAD//70ZBAAABXwAAAsDAAAAA//+9GQQAAAV+AAAHAwAAAAD//70ZBAAABYAAAAgDAAAAA//+9GQQAAAWCAAAkDAAAAA//+9GQQAAAWGAAArAwAAAAD//70ZBAAABWwAAAsDAAAAAD" type="audio/mp3">
                        </audio>
                    """
                    st.components.v1.html(beep_html, height=0)
                    
                    # Smart Alert Logging
                    engagement_score = (attentive_count/len(faces)) * 100
                    if engagement_score < 50:
                        # Prevent duplicate alerts in the same session to avoid DB spam
                        alert_key = f"alert_{room_source}_{st.session_state.get('username')}"
                        if st.session_state.get(alert_key) != True:
                            db.log_system_alert(
                                alert_type="Critical", 
                                message=f"Low Engagement detected ({engagement_score:.1f}%). Students appear drowsy or distracted.",
                                room=room_source
                            )
                            st.session_state[alert_key] = True
                            st.toast("🚨 Critical Alert sent to Admin Dashboard!")
                
                st.image(img_array, caption=f"AI Vision Overlay: Remote Feed {room_source}", use_container_width=True)
                if attentive_count > (len(faces) * 0.7):
                    st.balloons()
        except Exception as e:
            st.error(f"Hardware Logic Error: {e}")

# Sidebar controls preserved
st.sidebar.markdown("---")
st.sidebar.subheader("🔊 System Audio")
enable_audio = st.sidebar.checkbox("Enable Audio Alerts", value=True, help="Must be enabled to hear the Focus Alerts.")

if st.sidebar.button("🔔 Test Alert (Click to Unlock Audio)"):
    beep_html = """
        <audio autoplay>
            <source src="data:audio/mp3;base64,SUQzBAAAAAABAFRYWFgAAAASAAADbWFqb3JfYnJhbmQAZGFzaABUWFhYAAAAEAAAA21pbm9yX3ZlcnNpb24AMABUWFhYAAAAHAAAA2NvbXBhdGlibGVfYnJhbmRzAGlzbzZtcDQxAFRTU0UAAAAPAAADTGF2ZjYwLjEwMC4xMDAAAAAAAAAAAAAAA//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAExpbmUAb3V0cHV0AD//vwZBAAABGIAAAMDAAAAA//+8GQQAAASiAAAHAwAAAAD//7wZBAAABIwAAAkDAAAAA//+8GQQAAAS8AAArAwAAAAD//7wZBAAABMAAAAsDAAAAA//+9GQQAAATWAAAHAwAAAAD//70ZBAAABOgAAAgDAAAAA//+9GQQAAAT6AAAkDAAAAA//+9GQQAAAUmAAArAwAAAAD//70ZBAAABSwAAAsDAAAAA//+9GQQAAAVmAAAHAwAAAAD//70ZBAAABWgAAAgDAAAAA//+9GQQAAAVwAAAkDAAAAA//+9GQQAAAV4AAArAwAAAAD//70ZBAAABXwAAAsDAAAAA//+9GQQAAAV+AAAHAwAAAAD//70ZBAAABYAAAAgDAAAAA//+9GQQAAAWCAAAkDAAAAA//+9GQQAAAWGAAArAwAAAAD//70ZBAAABWwAAAsDAAAAAD" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(beep_html, height=0)
    st.toast("System: Audio Context Unlocked! ✅")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ AI Analytics Sensitivity")
face_thresh = st.sidebar.slider("Face Detection Threshold", 1, 10, 5)
eye_thresh = st.sidebar.slider("Eye Detection Sensitivity", 1.1, 1.5, 1.25)
